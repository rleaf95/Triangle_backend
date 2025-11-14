from django.db import transaction
from django.core.exceptions import ValidationError
import requests, jwt
import requests
from core.models import User, CustomerRegistrationProgress
from .user_registration_service import  RegistrationUtilsService
from django.core.cache import cache
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Q

class SocialLoginService:
  """ソーシャルログイン専用サービス"""
  
  @classmethod
  @transaction.atomic
  def get_or_create_user( cls, user_type, access_token, provider, session_token=None, id_token=None):

    if provider == 'google':
      social_user_data = cls._get_google_user_data(access_token)
    elif provider == 'line':
      social_user_data = cls._get_line_user_data(access_token, id_token)
    elif provider == 'facebook':
      social_user_data = cls._get_facebook_user_data(access_token)
    else:
      raise ValueError(f"未対応のプロバイダー: {provider}")
    
    social_id = social_user_data['id']
    email = social_user_data['email']
    picture = social_user_data.get('picture', '')
    user_id_field = f'{provider}_user_id'
    email_verified = social_user_data['email_verified']
    existing_user = User.objects.filter(Q(**{user_id_field: social_id}) | Q(email=email)).first()

    ## 1 既存ユーザーあり
    if existing_user:
      existing_social_id = getattr(existing_user, user_id_field, None)

      # ケース1-1: 既に同じソーシャルアカウントが紐づいている
      if existing_social_id == social_id:
        return cls._handle_existing_social_user(existing_user, email, provider, picture, email_verified)
      
      # ケース1-2: 別のソーシャルアカウントが紐づいている
      elif existing_social_id:
        raise ValidationError( f'既に別の{provider.capitalize()}アカウントが紐づいています')
      
      # ケース1-3: ソーシャルアカウント未紐付け
      else:
        # スタッフの招待アクティベート
        if session_token and user_type == 'STAFF':
          return cls._handle_activate_social( session_token, provider, social_user_data )
        
        # 既存ユーザーにソーシャルアカウントを追加
        return cls._add_social_to_existing_user(existing_user, provider, social_id, picture, email_verified)
    
    # 2. 既存ユーザーなし → 新規登録
    else:
      if user_type in ['CUSTOMER', 'OWNER']:
        return cls._handle_signup_social(user_type, provider, social_user_data)
      else:
        raise ValidationError("スタッフの登録には招待が必要です。")
      
  @classmethod
  def _check_existing_user(cls, user, provider, picture, email_verified ):
    update_fields = []

    if user.auth_provider != provider:
      user.auth_provider = provider
      update_fields.append('auth_provider')
    
    if picture and not user.profile_image_url:
      user.profile_image_url = picture
      update_fields.append('profile_image_url')
    
    if not user.is_active:
      user.is_email_verified = email_verified
      user.is_active = email_verified
      update_fields.append('is_email_verified')
      update_fields.append('is_active')
    
    return update_fields

  
  @classmethod
  def _add_social_to_existing_user(cls, existing_user, provider, social_id, picture, email_verified):
    
    user_id_field = f'{provider}_user_id'
    update_fields = cls._check_existing_user(existing_user, provider, picture, email_verified )
    
    setattr(existing_user, user_id_field, social_id)
    update_fields.append(user_id_field)
    existing_user.save(update_fields=update_fields)

    if not existing_user.is_active:
      return existing_user, None, 'メール認証リンクを送信しました。メールを確認してください。'
    refresh = RefreshToken.for_user(existing_user)
    return existing_user, refresh, f'{provider.capitalize()}アカウントを追加しました'


  @classmethod
  def _handle_existing_social_user(cls, existing_user, email, provider, picture, email_verified ):
    update_fields = cls._check_existing_user(existing_user, provider, picture, email_verified )

    if existing_user.email != email:
      existing_user.email = email
      update_fields.append('email')
    if update_fields:
      existing_user.save(update_fields=update_fields)
    
    if not existing_user.is_active:
      return existing_user, None, 'メール認証リンクを送信しました。メールを確認してください。'
    refresh = RefreshToken.for_user(existing_user)
    return existing_user, refresh, f'{provider.capitalize()}アカウントでログインしました'
  

  @classmethod
  def _handle_signup_social(cls, user_type, provider, social_user_data):
    user_id_field = f'{provider}_user_id'
    user_data = {
      'email': social_user_data['email'],
      'user_type': user_type,
      'auth_provider': provider,
      'is_active': social_user_data['email_verified'],
      'is_email_verified': social_user_data['email_verified'],
      'first_name': social_user_data.get('first_name', ''),
      'last_name': social_user_data.get('last_name', ''),
      'profile_image_url': social_user_data.get('picture', ''),
      user_id_field: social_user_data['id']
    }
    
    user = User.objects.create(**user_data)
    refresh = RefreshToken.for_user(user)

    if user_type == 'CUSTOMER':
      progress = CustomerRegistrationProgress.objects.get(user=user)  # 1クエリ
      user._cached_customer_progress = progress
    
    if user.is_active == False:
      return user, None, 'メール認証リンクを送信しました。メールを確認してください。'
    refresh = RefreshToken.for_user(user)
    return user, refresh, f'{provider.capitalize()}でアカウントを作成しました'


  @classmethod
  def _handle_activate_social(cls, session_token, provider, data):

    invitation = RegistrationUtilsService.get_invitation_from_session(session_token)
    user_id_field = f'{provider}_user_id'

    user = invitation.user
    setattr(user, user_id_field, data['id'])
    user.is_active = True
    user.is_email_verified = True
    user.auth_provider = provider
    user.user_type = 'STAFF'
    user.profile_image_url = data['picture']
    user.save()

    return RegistrationUtilsService.complete_activation(user, invitation, session_token)

  @classmethod
  def _get_google_user_data(cls, access_token):
    try:
      response = requests.get(
        'https://www.googleapis.com/oauth2/v2/userinfo',
        headers={"Authorization": f"Bearer {access_token}"}
      )
      response.raise_for_status()
    except requests.exceptions.HTTPError:
        raise ValidationError("Googleトークンが無効です。再ログインしてください。")
    
    data = response.json()

    if not data.get('id') or not data.get('email'):
      raise ValidationError("Googleからメールアドレスを取得できませんでした。")
    
    return {
      'id': data['id'],
      'email': data['email'],
      'first_name': data.get('given_name', ''),
      'last_name': data.get('family_name', ''),
      'picture': data.get('picture', ''),
      'email_verified': data.get('verified_email', False)
    }
  
  @classmethod
  def _get_facebook_user_data(cls, access_token):
    try:
      response = requests.get(
        'https://graph.facebook.com/me',
        params={ 
          'fields': 'id,email,first_name,last_name,name,picture,email_verified', 
          'access_token': access_token
					}
      )
      response.raise_for_status()
    except requests.exceptions.HTTPError:
        raise ValidationError("Facebookトークンが無効です。再ログインしてください。")
    
    data = response.json()

    if not data.get('id') or not data.get('email'):
      raise ValidationError("facebookからメールアドレスを取得できませんでした。")
    
    return {
      'id': data['id'],
      'email': data['email'],
      'first_name': data.get('first_name', ''),
      'last_name': data.get('last_name', ''),
      'picture': data.get('picture', {}).get('data', {}).get('url', ''),
      'email_verified' : data.get('email_verified', False)
    }
  
  @classmethod
  def _get_line_user_data(cls, access_token, id_token):
    if not access_token:
      raise ValidationError("アクセストークンが必要です")
    if not id_token:
      raise ValidationError("IDトークンが必要です")
    
    try:
      response = requests.get(
          'https://api.line.me/v2/profile',
          headers={'Authorization': f'Bearer {access_token}'}
      )
      response.raise_for_status()
      profile_data = response.json()
      
      payload = jwt.decode(id_token, options={"verify_signature": False})
        
    except requests.exceptions.HTTPError:
      raise ValidationError("LINEトークンが無効です。再ログインしてください。")
    except (jwt.exceptions.DecodeError, jwt.exceptions.InvalidTokenError, Exception) as e:
      raise ValidationError("LINEトークンが無効です。再ログインしてください。")
    
    if not payload.get("sub") and not profile_data.get("userId"):
      raise ValidationError("LINEからユーザー情報を取得できませんでした。")
    
    if not payload.get("email"):
      raise ValidationError("LINEからメールアドレスを取得できませんでした。")
    
    return {
      "id": payload.get("sub") or profile_data.get("userId"),
      "name": profile_data.get("displayName"),
      "email": payload["email"],
      "picture": profile_data.get("pictureUrl"),
      "email_verified": True
    }