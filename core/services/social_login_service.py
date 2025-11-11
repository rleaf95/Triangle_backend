from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from core.models import User
from .user_registration_service import UserRegistrationService
from .profile_service import ProfileService


class SocialLoginService:
  """ソーシャルログイン専用サービス"""
  
  @staticmethod
  @transaction.atomic
  def get_or_create_user(validated_user_type, provider, uid, social_data, form_data=None, invitation=None):

    existing_user = User.objects.find_by_social_id(provider, uid)
    email = social_data['email']
    picture = social_data['picture']
    user_id_field = f'{provider}_user_id'

    if existing_user:
      if existing_user.email != email:
        existing_user.email = email
        existing_user.save(update_fields=['email'])
        return existing_user, False, f'{provider.capitalize()}アカウントでログインしました'
    elif validated_user_type == 'STAFF':
      if invitation:
        registered_user, created, message = SocialLoginService._activate_staff_user_with_social(
          invitation=invitation,
          provider=provider,
          uid=uid,
          social_data=social_data, 
          form_data=form_data, 
        )
        UserRegistrationService.process_invitation(invitation, registered_user)
        return registered_user, created, message
      else:
        raise ValidationError("スタッフでの登録には招待が必要です")
    else:
      if email:
        existing_user_by_email = User.objects.find_by_email(email)
        if existing_user_by_email:
          setattr(existing_user_by_email, user_id_field, uid)
          existing_user_by_email.auth_provider = provider
          update_fields = [user_id_field, 'auth_provider']

          if picture and not existing_user_by_email.profile_image_url:
            existing_user_by_email.profile_image_url = picture
            update_fields.append('profile_image_url')

          existing_user_by_email.save(update_fields=update_fields)
          return existing_user_by_email, False, f'{provider.capitalize()}アカウントを追加しましたしました'
        else:
          registered_user, created, message = SocialLoginService._create_new_user_with_social(
            validated_user_type,
            provider=provider,
            uid=uid,
            social_data=social_data,
            invitation=invitation
          )
          registered_user.set_unusable_password()
          return registered_user, created, message
      else:
        raise ValidationError("ユーザー情報を取得できませんでした。")
        #別のアカウント、social mediaを試してもらうか、email登録

  
  @staticmethod
  def extract_social_data(provider, extra_data):
    social_data = {
        'first_name': '',
        'last_name': '',
        'email': '',
        'email_verified': False,
        'picture': '',
        'language': 'ja'
    }
    
    if provider == 'google':
        social_data['first_name'] = extra_data.get('given_name', '')
        social_data['last_name'] = extra_data.get('family_name', '')
        social_data['email'] = extra_data.get('email', '')
        social_data['email_verified'] = extra_data.get('email_verified', False)
        social_data['picture'] = extra_data.get('picture', '')
        locale = extra_data.get('locale', 'ja')
        social_data['language'] = locale[:2] if locale else 'ja'
        
    elif provider == 'apple':
        # Appleは初回のみ名前を提供
        name = extra_data.get('name', {})
        if isinstance(name, dict):
            social_data['first_name'] = name.get('firstName', '')
            social_data['last_name'] = name.get('lastName', '')
        
        social_data['email'] = extra_data.get('email', '')
        
        # email_verifiedは文字列 'true'/'false' の場合もあるので変換
        email_verified = extra_data.get('email_verified', False)
        if isinstance(email_verified, str):
            social_data['email_verified'] = email_verified.lower() == 'true'
        else:
            social_data['email_verified'] = bool(email_verified)
        
        social_data['picture'] = ''
        social_data['language'] = 'ja'
        
    elif provider == 'facebook':
        social_data['first_name'] = extra_data.get('first_name', '')
        social_data['last_name'] = extra_data.get('last_name', '')
        social_data['email'] = extra_data.get('email', '')
        social_data['email_verified'] = True  # Facebookは常に確認済みメールのみ提供
        
        picture_data = extra_data.get('picture', {})
        if isinstance(picture_data, dict):
            data = picture_data.get('data', {})
            social_data['picture'] = data.get('url', '')
        
        locale = extra_data.get('locale', 'ja_JP')
        social_data['language'] = locale[:2] if locale else 'ja'
    
    return social_data
    
  @staticmethod
  def _activate_staff_user_with_social(invitation, provider, uid, social_data, form_data):
    if not hasattr(invitation, 'user') or not invitation.user:
      raise ValidationError("招待にユーザー情報が含まれていません")
    
    user = invitation.user
    if user.is_active:
      raise ValidationError("このユーザーは既に登録済みです")
    
    user_id_field = f'{provider}_user_id'
    user.email = social_data['email']

    setattr(user, user_id_field, uid)
    user.auth_provider = provider
    
    user.is_active = True
    user.is_email_verified = True
    user.user_type = 'STAFF'
    user.language = form_data['language'] or invitation.language
    user.phone_number = form_data['phone_number']

    if not user.first_name:
      user.first_name = social_data['first_name']
    if not user.last_name:
      user.last_name = social_data['last_name']

    if social_data['picture']:
      user.profile_image_url = social_data['picture']
    
    user.save()

    profile_data = {}
    for field in ['address', 'suburb', 'state', 'post_code']:
      if field in form_data:
        profile_data[field] = form_data[field]
    
    ProfileService.get_or_create_staff_profile(user, **profile_data)
    
    return user, True, f'{provider.capitalize()}でアカウントをアクティベートしました'
  
  @staticmethod
  def _create_new_user_with_social( validated_user_type, provider, uid, social_data, invitation):
    
    user_id_field = f'{provider}_user_id'
    # ユーザー作成用のデータを準備
    user_data = {
      'email': social_data['email'],
      'user_type': validated_user_type,
      'auth_provider': provider,
      'is_active': True,
      'is_email_verified': True,
      'first_name': social_data['first_name'] or '',
      'last_name': social_data['last_name'] or '',
      'profile_image_url': social_data['picture'] or '',
      user_id_field: uid
    }
    # ユーザーを作成
    user = User.objects.create(**user_data)
    
    user.save()
    
    return user, True, f'{provider.capitalize()}でアカウントを作成しました'
  
  
  @staticmethod
  def prepare_user_data_from_form(form):

    result = {
      'phone_number': None,
      'language': None,
      'profile_data': {}
    }
    
    if not form or not hasattr(form, 'cleaned_data'):
      return result
    
    cleaned_data = form.cleaned_data
    
    result['language'] = cleaned_data.get('language') or None
    result['phone_number'] = cleaned_data.get('phone_number') or None
    
    for field in ['address', 'suburb', 'state', 'post_code']:
      if field in cleaned_data:
        value = cleaned_data[field]
        if value:
          result['profile_data'][field] = value
  
    return result
    
    