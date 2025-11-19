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
from authentication.models import PendingUser
import secrets
from datetime import timedelta
from django.contrib.auth.hashers import make_password
from .email_service import RegistrationEmailService

class UserRegistrationService:

  @classmethod
  def register_pending_user(cls, email, password, user_type, country, timezone):

    PendingUser.objects.filter(email=email).delete()

    existing_user = User.objects.email_exists_in_group(email, user_type)

    if existing_user:
      if existing_user.has_usable_password():
        raise ValidationError('すでに登録済みのアドレスです。ログインしてください。')
    
    token = secrets.token_urlsafe(32)
    expires_at = timezone.now() + timedelta(hours=24)
    
    pending_user = PendingUser.objects.create(
      user = existing_user if existing_user else None,
      email=email,
      password_hash=make_password(password),
      user_type=user_type,
      verification_token=token,
      token_expires_at=expires_at,
      country=country,
      timezone=timezone
    )

    success, error_message = RegistrationEmailService.send_registration_confirmation(pending_user)

    if success:
      if existing_user:
        return pending_user, True, '既存のアカウントが見つかりました。セキュリティのため、メールアドレスの確認をお願いします'
      
      return pending_user, False, 'メールアドレス認証メールを送信しました。メールを確認してください。'
    else:
      raise ValidationError(error_message)
  
  @classmethod
  def verify_and_activate(cls, token):
    try:
      pending_user = PendingUser.objects.get(verification_token=token)
    except PendingUser.DoesNotExist:
      raise ValidationError('無効な確認リンクです')
    
    if not pending_user.is_token_valid():
      raise ValidationError('確認リンクの有効期限が切れています')
    
    user_type = pending_user.user_type
    if pending_user.user != None:
      user = pending_user.link_social_account()
      return user, True, 'パスワードの設定が完了しました。'
    
    user = pending_user.create_user()
    if user_type == 'CUSTOMER':
      progress = CustomerRegistrationProgress.objects.get(user=user)
      user._cached_customer_progress = progress

    # if user_type == 'OWNER':
    #   cls.create_user_relationships(user)  
    
    return user, False, '登録が完了しました'
  
  
  @classmethod
  def resend_verification_email(cls, email):

    try:
      pending_user = PendingUser.objects.get(email=email)
    except PendingUser.DoesNotExist:
      raise ValidationError('登録が見つかりません。もう一度やり直してください。')
    
    pending_user.verification_token = secrets.token_urlsafe(32)
    pending_user.token_s = timezone.now() + timedelta(hours=24)
    pending_user.save()

    success, error_message = RegistrationEmailService.resend_confirmation(pending_user)

    if success:
      return pending_user
    else:
      raise ValidationError(error_message)
  

  @classmethod
  def change_pending_email(cls, old_email, new_email):
    try:
      pending_user = PendingUser.objects.get(email=old_email)
    except PendingUser.DoesNotExist:
      raise ValidationError('登録が見つかりません')
    
    pending_user.email = new_email
    pending_user.verification_token = secrets.token_urlsafe(32)
    pending_user.token_expires_at = timezone.now() + timedelta(hours=24)
    pending_user.save()
    
    success, error_message = RegistrationEmailService.send_email_change_confirmation(pending_user, new_email)
    
    if success:
      return pending_user
    else:
      raise ValidationError(error_message)
  
  
    
###今日すること###
# ソーシャルメディアの実装を過去のチャットからアイデア持ってきて実装
# テストの実装
# 仕様書作るー多言語対応の設定を同時に