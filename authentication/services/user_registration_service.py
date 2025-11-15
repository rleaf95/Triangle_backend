# core/services/user_registration_service.py

from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db import transaction, IntegrityError
from users.models import User, CustomerRegistrationProgress
from invitation.models import StaffInvitation
from users.service.profile_service import ProfileService
from django.core.cache import cache
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Q
from .registration_utils_service import RegistrationUtilsService

class UserRegistrationService:
  
  @classmethod
  @transaction.atomic
  def register_user(cls, session_token, user_type, data):

    if session_token and user_type == 'STAFF':
      return cls._handle_activate( session_token, data )
    elif not session_token and user_type == 'CUSTOMER' or user_type == 'OWNER':
      return  cls._handle_signup( user_type, data )
    else :
      raise ValidationError("許可されていない登録です")
      
  
  @classmethod
  def _handle_signup(cls, user_type, data):

    email = data.get('email')
    existing_user = User.objects.find_by_email(email)

    if existing_user:
      if existing_user.has_usable_password():
        raise ValidationError('すでに登録済みのアドレスです。ログインしてください。')
      return cls._handle_link_social_account(existing_user, data)

    user = User.objects.create_user(
      email=data.get('email'),
      password=data.get('password'),
      user_type=user_type,
      country=data.get('country', ''),
      timezone=data.get('timezone', ''),
      language=data.get('language',''),
      auth_provider='email',
      first_name=data.get('first_name', ''),
      last_name=data.get('last_name',''),
      phone_number=data.get('phone_number',''),
      is_email_verified = False,
      profile_image = data.get('picture',''),
      is_active = False
    )

    if user_type == 'CUSTOMER':
      progress = CustomerRegistrationProgress.objects.get(user=user)
      user._cached_customer_progress = progress

    if user_type == 'OWNER':
      cls.create_user_relationships(user)  
    
    return user, None, 'メール認証リンクを送信しました。メールを確認してください。'
  
  @classmethod
  def _handle_link_social_account(cls, existing_user, data):
    
    password = data.get('password')
    if not password:
      raise ValidationError('パスワードを設定してください。')
    
    existing_user.set_password(password)
    existing_user.auth_provider = 'email'
    update_fields = ['password', 'auth_provider']
    
    existing_user.save(update_fields=update_fields)

    return ( existing_user, None, 'メール認証リンクを送信しました。メールを確認後、パスワードでもログインできます。')
    
  
  @classmethod
  def _handle_activate(cls, session_token, data):
    required_fields = ['password', 'email']
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
      raise ValidationError(f"必須フィールドが不足しています: {', '.join(missing_fields)}")

    invitation = RegistrationUtilsService.get_invitation_from_session(session_token)

    user = invitation.user
    password = data['password']
    user.set_password(password)
    user.is_active = True
    user.is_email_verified = True
    user.auth_provider = 'email'
    user.profile_image = data.get('picture', '')

    user.save(update_fields=[
      'password', 'is_active', 'is_email_verified', 'auth_provider', 'profile_image'
    ])

    return RegistrationUtilsService.complete_activation(user, invitation, session_token)

  

  @classmethod
  def handle_profile_creation(cls, user, profile_data=None):
    """プロファイル作成・更新の共通処理"""
    if profile_data:
      if user.user_type == 'STAFF':
        ProfileService.get_or_create_staff_profile(user, profile_data)
      else:
        pass
    

  
  @classmethod
  def create_user_relationships(cls, user):
    """
    ユーザーと会社・テナントの関連を作成（オーナー用）
    """
    if user.user_type == 'OWNER':
      cls._create_owner_relationships(user)
    else:
      pass
  
  @classmethod
  def _create_owner_relationships(cls, user):
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
  
  @classmethod
  def process_invitation(cls, invitation, user):
    """招待を処理（使用済みにする）"""
    if invitation:
      invitation.is_used = True
      invitation.registered_user = user
      invitation.used_at = timezone.now()
      invitation.save()
    
