"""
ユーザー登録の共通ロジック
→ SerializerとAdapterの両方から呼び出す
"""
from django.core.exceptions import ValidationError
from django.utils import timezone
from core.models import User, StaffInvitation
from core.services.profile_service import ProfileService

class UserRegistrationService:
    
  """招待トークンの検証"""
  @staticmethod
  def validate_invitation(invitation_token):
    if not invitation_token:
      return None
    
    try:
      invitation = StaffInvitation.objects.get(
        token=invitation_token,
        is_used=False,
        expires_at__gt=timezone.now()
      )
      return invitation
    except StaffInvitation.DoesNotExist:
      raise ValidationError('無効な招待リンクです')
  
  """ユーザータイプの検証"""
  @staticmethod
  def validate_user_type(user_type, invitation):
    if invitation:
      return 'STAFF'
    
    if user_type == 'STAFF':
      raise ValidationError('スタッフの登録には招待が必要です')
    
    return user_type
    
  """ユーザー作成"""
  @staticmethod
  def create_user(email, password, user_type, language='en', country='AU', auth_provider='email', invitation=None):
    # 招待がある場合、招待情報を優先
    if invitation:
      user_type = 'STAFF',
      language = invitation.language or language,
      country = invitation.country
    else:
      user = User.objects.create_user(
        email=email,
        password=password,
        user_type=user_type,
        language=language,
        auth_provider=auth_provider,
        country=country
      )
      
      user.save()
      
      return user
    
    """招待処理（使用済みにする）"""
  @staticmethod
  def process_invitation(invitation, user):
    if not invitation:
      return
    
    invitation.is_used = True
    invitation.registered_user = user
    invitation.used_at = timezone.now()
    invitation.save()
  
  """ユーザー登録の完全なフロー → SerializerとAdapterの両方から呼び出す"""
  @classmethod
  def register_user(cls, email, password, user_type, language='ja', auth_provider='email', invitation_token=None, profile_data=None):
    # 1. 招待検証
    invitation = cls.validate_invitation(invitation_token)
    # 2. ユーザータイプ検証
    validated_user_type = cls.validate_user_type(user_type, invitation)
    # 3. ユーザー作成
    user = cls.create_user(
      email=email,
      password=password,
      user_type=validated_user_type,
      language=language,
      auth_provider=auth_provider,
      invitation=invitation
    )
    # 4. プロファイル作成
    if profile_data:
      if user.user_type == 'OWNER':
          ProfileService.update_owner_profile(user, **profile_data)
      elif user.user_type == 'STAFF':
          ProfileService.update_staff_profile(user, **profile_data)
    else:
      # 空のプロファイルを作成
      if user.user_type == 'OWNER':
        ProfileService.get_or_create_owner_profile(user)
      elif user.user_type == 'STAFF':
        ProfileService.get_or_create_staff_profile(user)
    
    # 5. 招待処理
    cls.process_invitation(invitation, user)
    
    return user, invitation