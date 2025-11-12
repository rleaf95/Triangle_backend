# core/services/user_registration_service.py

from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db import transaction
from core.models import User, StaffInvitation, TenantMembership
from core.services.profile_service import ProfileService
from django.core.cache import cache
from rest_framework_simplejwt.tokens import RefreshToken


class UserRegistrationService:
  
  @classmethod
  @transaction.atomic
  def register_user(cls, session_token, user_type, data, profile_data):

    if session_token and user_type == 'STAFF':
      return cls._handle_activate( session_token, data, profile_data )
    elif user_type == 'CUSTOMER' or user_type == 'OWNER':
      return  cls._handle_signup( user_type, data, profile_data )
    else :
      raise ValidationError("許可されていない登録です")
      
  
  @classmethod
  @transaction.atomic
  def _handle_signup(cls, user_type, data, profile_data):

    user = User.objects.create_user(
      email=data['email'],
      password=data['password'],
      user_type=user_type,
      country=data['country', ''],
      timezone=data['country', ''],
      auth_provider='email',
      first_name=data['first_name', ''],
      last_name=data['last_name',''],
      phone_number=data['phone_number',''],
      is_email_verified = False,
      picture = data['picture','']
    )
    
    user.save()
    if profile_data:
      cls.handle_profile_creation(user, profile_data)
    if user_type == 'OWNER':
      cls.create_user_relationships(user)  
    
    return user, None, 'メール認証リンクを送信しました。メールを確認してください。'
  
  
  @classmethod
  def _handle_activate(cls, session_token, data, profile_data):
    cache_key = f'invitation_session:{session_token}'
    session_data = cache.get(cache_key)

    if not session_data:
      raise ValidationError("セッションが無効または期限切れです。もう一度招待リンクからアクセスしてください。")
    
    invitation_id = session_data.get('invitation_id')
    invitation_token = session_data.get('invitation_token')
    session_email = session_data.get('email')

    try:
      invitation = (StaffInvitation.objects
        .with_related_info
        .valid
        .by_token(invitation_token)
        .by_email.valid(session_email)
        .by_id(invitation_id))
    except StaffInvitation.DoesNotExist:
      cache.delete(cache_key)
      raise ValidationError('招待が見つかりません')
    
    user = invitation.user

    user.is_active = True
    user.is_email_verified = True
    user.auth_provider = 'email'
    user.password=data['password']
    user.language = data['language']
    user.user_type = 'STAFF'
    user.first_name = data['first_name']
    user.last_name = data['last_name']
    user.phone_number = data['phone_number', '']
    user.profile_image_url = data['picture', '']
    user.save()

    cache.delete(cache_key)
    refresh = RefreshToken.for_user(user)
    cls.handle_profile_creation(user, profile_data)
    cls.process_invitation(invitation, user)
    
    return user, refresh, 'USERをアクティベートしました'
  
  def validate_invitation(invitation_token):
    try:
      invitation = StaffInvitation.objects.valid().by_token(invitation_token).get()
      return invitation
    except StaffInvitation.DoesNotExist:
        raise ValidationError('無効または期限切れの招待リンクです')
  

  @classmethod
  def handle_profile_creation(cls, user, profile_data=None):
    """プロファイル作成・更新の共通処理"""
    if profile_data:
      if user.user_type == 'STAFF':
        ProfileService.get_or_create_staff_profile(user, **profile_data)
      else:
        pass
    

  
  @classmethod
  def create_user_relationships(cls, user, invitation):
    """
    ユーザーと会社・テナントの関連を作成（オーナー用）
    """
    if user.user_type == 'OWNER':
      cls._create_owner_relationships(user, invitation)
    else:
      pass
  
  @classmethod
  def _create_owner_relationships(cls, user, invitation):
    """
    オーナーの関連を作成
    
    新規登録の場合は後で会社作成時に紐付けるため、ここでは何もしない
    """
    # TODO: 必要に応じて実装
    pass
  
  @classmethod
  def _create_customer_relationships(cls, user):
    """カスタマーの関連を作成"""
    # TODO: 必要に応じて実装
    pass
  
  @staticmethod
  def process_invitation(invitation, user):
    """招待を処理（使用済みにする）"""
    if invitation:
      invitation.is_used = True
      invitation.registered_user = user
      invitation.used_at = timezone.now()
      invitation.save()
    