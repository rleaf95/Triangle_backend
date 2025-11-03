# core/services/social_login.py
from core.services.user_registration import UserRegistrationService
from core.services.profile_service import ProfileService

"""ソーシャルログイン共通処理"""
class SocialLoginService:
  @staticmethod
  def get_or_create_user(request, email, social_user_id, provider, first_name='', last_name='', picture='', invitation_token=None, registration_type=None):
    """ソーシャルログインでユーザー取得または作成"""
    from core.models import User
    
    # プロバイダーIDで検索
    user_id_field = f'{provider}_user_id'

    try:
      user = User.objects.get(**{user_id_field: social_user_id})
      created = False
      if user.email != email:
        user.email = email
        user.save()
      
      return user, created
        
    except User.DoesNotExist:
      
      try:
        user = User.objects.get(email=email)
        setattr(user, user_id_field, social_user_id)
        user.save()
        return user, False
        
      except User.DoesNotExist:

        invitation = UserRegistrationService.validate_invitation(invitation_token)
        if invitation:
          user_type = 'STAFF'
        else:
          user_type = request.session.get('registration_type', 'customer')   

        # ユーザー作成
        user = User.objects.create(
          email=email,
          user_type=user_type,
          auth_provider=provider,
          is_email_verified=True,
          profile_image_url=picture,
          **{user_id_field: social_user_id}
        )

        if invitation:
          user.language = invitation.language or 'ja'
          user.country = invitation.country
          user.save()
          UserRegistrationService.process_invitation(invitation, user)

        profile, profile_created = SocialLoginService._create_profile(
          user,
          first_name=first_name,
          last_name=last_name,
          invitation=invitation
        )
        
        return user, True
  
  """
  ソーシャルログイン時のプロファイル作成
  Args:
    user: Userオブジェクト
    first_name: 名
    last_name: 姓
    invitation: 招待オブジェクト（スタッフの場合）
  Returns:
    tuple: (profile, created)
  """
  @staticmethod
  def _create_profile(user, first_name='', last_name='', invitation=None):
    profile_data = {}
    if first_name:
      profile_data['first_name'] = first_name
    if last_name:
      profile_data['last_name'] = last_name
    
    if user.user_type == 'OWNER':
      profile, created = ProfileService.get_or_create_owner_profile(
        user,
        **profile_data
      )
      return profile, created
    elif user.user_type == 'STAFF':        
      profile, created = ProfileService.get_or_create_staff_profile(
        user,
        **profile_data
      )
      return profile, created
    
    elif user.user_type == 'CUSTOMER':
      return None, False
    
    return None, False
    
  """
  プロフィール画像をダウンロードして保存（オプション）
  
  Args:
      user: Userオブジェクト,画像フィールドを持つ
      image_url: 画像URL
  
  Returns:
      bool: 成功した場合True、失敗した場合False
  """
  @staticmethod
  def _download_profile_image(user, image_url):
    try:
      import requests
      from django.core.files.base import ContentFile
      from urllib.parse import urlparse
      import uuid
      
      response = requests.get(image_url, timeout=5)
      if response.status_code == 200:
        ext = urlparse(image_url).path.split('.')[-1] or 'jpg'
        filename = f"profile_{user.id}_{uuid.uuid4().hex[:8]}.{ext}"
        
        user.profile_image.save(
          filename,
          ContentFile(response.content),
          save=True
        )
        return True
    except Exception as e:
      print(f"プロフィール画像のダウンロードに失敗: {e}")
    
    return False