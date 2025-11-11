# core/services/user_registration_service.py

from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db import transaction
from core.models import User, StaffInvitation, TenantMembership
from core.services.profile_service import ProfileService


class UserRegistrationService:
  """ユーザー登録の共通ロジック"""
  
  @classmethod
  @transaction.atomic
  def register_user(
    cls, email, password, user_type, language='ja', country='AU', invitation_token=None, profile_data=None, 
    timezone=None, first_name='', last_name='', picture=None, phone_number=None,
    ):
    """
    完全な登録フロー（新規ユーザー作成から全て）
    """
    invitation = cls.validate_invitation(invitation_token)
    validated_user_type = cls.validate_user_type(user_type, invitation)

    if validated_user_type == 'STAFF':
      user_data = {
        'email': email,
        'password': password,
        'first_name': first_name,
        'last_name': last_name,
        'phone_number': phone_number,
        'picture': picture,
        'language': language,
        'country': country,
        'auth_provider': 'email',
      }
      user = cls.activate_staff_user( invitation, user_data, profile_data)
    else:
      if User.objects.filter(email=email).exists():
        raise ValidationError("このメールアドレスは既に登録されています")
      
      user = User.objects.create_user(
        email=email,
        password=password,
        user_type=validated_user_type,
        language=language,
        country=country,
        timezone=timezone,
        auth_provider='email',
        first_name=first_name,
        last_name=last_name,
        phone_number=phone_number,
        is_email_verified = True
      )
      
      if picture:
        user.profile_image_url = picture
        user.save(update_fields=['profile_image_url'])
    
    cls.handle_profile_creation(user, profile_data)
    cls.create_user_relationships(user, invitation)
    cls.process_invitation(invitation, user)
    
    return user, invitation
  
  @classmethod
  @transaction.atomic
  def complete_user_registration(cls, user, validated_user_type, invitation=None, profile_data=None):
    user.user_type = validated_user_type
    user.auth_provider = user.auth_provider or 'email'
    user.is_email_verified = True
    
    user.save()
    if profile_data:
      cls.handle_profile_creation(user, profile_data)
    
    if validated_user_type == 'OWNER':
      cls.create_user_relationships(user, invitation)
    
    if invitation:
      cls.process_invitation(invitation, user)
    
    return user
  
  
  #-------------------
  #Helper method
  #-------------------
  @classmethod
  def activate_staff_user(cls, invitation, user_data, profile_data=None):
    """
    既存のスタッフユーザーをアクティベート
    Returns:User: アクティベートされたユーザー
    """
    if not invitation:
      raise ValidationError("スタッフの登録には招待が必要です")
    
    if not hasattr(invitation, 'user') or not invitation.user:
      raise ValidationError("招待にユーザー情報が含まれていません")
    
    user = invitation.user
    
    if user.is_active:
      raise ValidationError("このユーザーは既に登録済みです")
    
    # パスワードを設定
    if user_data.get('password'):
      user.set_password(user_data['password'])
    
    # ユーザー情報を更新
    user.is_active = True
    user.is_email_verified = True
    user.auth_provider = user_data.get('auth_provider', 'email')
    user.language = user_data.get('language') or invitation.language or user.language
    user.country = user_data.get('country') or invitation.country or user.country
    user.email = user_data.get('email', user.email)
    user.user_type = 'STAFF'
    user.first_name = user_data.get('first_name', user.first_name)
    user.last_name = user_data.get('last_name', user.last_name)
    user.phone_number = user_data.get('phone_number', user.phone_number)
    
    # プロフィール画像
    if user_data.get('picture'):
      user.profile_image_url = user_data['picture']
    
    user.save()
    
    cls.handle_profile_creation(user, profile_data)
    cls.process_invitation(invitation, user)
    
    return user
  
  @staticmethod
  def validate_invitation(invitation_token):
    """招待トークンの検証"""
    if not invitation_token:
      return None
    try:
      invitation = StaffInvitation.objects.with_related_info().valid().by_token(invitation_token).get()
      return invitation
    except StaffInvitation.DoesNotExist:
      raise ValidationError('無効または期限切れの招待リンクです')
  
  @staticmethod
  def validate_user_type(user_type, invitation):
    """ユーザータイプの検証"""
    if invitation:
      return 'STAFF'
    if user_type == 'STAFF':
      raise ValidationError('スタッフの登録には招待が必要です')
    
    valid_types = ['OWNER', 'CUSTOMER']
    if user_type not in valid_types:
      raise ValidationError(f"無効なユーザータイプです: {user_type}")
    return user_type
  
  @classmethod
  def handle_profile_creation(cls, user, profile_data=None):
    """プロファイル作成・更新の共通処理"""
    if profile_data:
      if user.user_type == 'STAFF':
        ProfileService.get_or_create_staff_profile(user, **profile_data)
      else:
        pass
    

  @staticmethod
  def create_user(email, password, user_type, timezone, first_name, last_name, phone_number, picture, language='en', country='AU', auth_provider='email'):
    """
    新規ユーザー作成（オーナー・カスタマー用）
    Returns:User: 作成されたユーザー
    """
    # メールアドレスの重複チェック
    if User.objects.filter(email=email).exists():
      raise ValidationError("このメールアドレスは既に登録されています")
    
    # ユーザー作成
    user = User.objects.create_user(
      email=email,
      password=password,
      user_type=user_type,
      language=language,
      country=country,
      timezone=timezone,
      auth_provider=auth_provider,
      first_name=first_name,
      last_name=last_name,
      phone_number=phone_number,
    )

    if picture:
      user.profile_image_url = picture
      user.save(update_fields=['profile_image'])
    
    return user
  
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
    