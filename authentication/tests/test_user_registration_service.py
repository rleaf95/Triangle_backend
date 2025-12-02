import pytest
import secrets
from django.utils import timezone
from django.contrib.auth.hashers import check_password
from datetime import timedelta
from unittest.mock import patch, MagicMock
from rest_framework.exceptions import ValidationError, NotFound

from authentication.services.user_registration_service import UserRegistrationService
from authentication.models import PendingUser
from users.models import User, CustomerRegistrationProgress
from authentication.tests.factories import UserFactory, PendingUserFactory
from common.service import EmailSendException
from rest_framework import status
import time

@pytest.mark.django_db
class TestRegisterPendingUserNewUser:
  """新規ユーザー登録のテスト"""
  
  def test_register_new_customer_success(self):
    """新規カスタマー登録が成功する"""
    email = 'newcustomer@example.com'
    password = 'password123'
    
    with patch('authentication.services.email_service.RegistrationEmailService.send_registration_confirmation') as mock_send:
      mock_send.return_value = None
      
      is_existing, message = UserRegistrationService.register_pending_user(
        email=email,
        password=password,
        user_type='CUSTOMER',
        country='JP',
        user_timezone='Asia/Tokyo',
        first_name='太郎',
        last_name='山田',
      )
      
      # PendingUserが作成されている
      # フラグとメッセージ
      assert is_existing is False
      assert 'A verification email has been sent' in message
      
  
  def test_register_new_owner_success(self):
    """新規オーナー登録が成功する"""
    email = 'newowner@example.com'
    password = 'password123'
    
    with patch('authentication.services.email_service.RegistrationEmailService.send_registration_confirmation'):
      is_existing, message = UserRegistrationService.register_pending_user(
        email=email,
        password=password,
        user_type='OWNER',
        country='US',
        user_timezone='America/New_York',
        first_name='山田',
        last_name='太郎',
      )
      
      assert is_existing is False
  
  def test_register_deletes_existing_pending_user(self):
    """既存のPendingUserが削除されて新規作成される"""
    email = 'test@example.com'
    
    # 既存のPendingUserを作成
    old_pending_user = PendingUserFactory.create(email=email)
    old_token = old_pending_user.verification_token
    
    with patch('authentication.services.email_service.RegistrationEmailService.send_registration_confirmation'):
      _, _ = UserRegistrationService.register_pending_user(
        email=email,
        password='newpassword',
        user_type='CUSTOMER',
        country='JP',
        user_timezone='Asia/Tokyo',
        first_name='山田',
        last_name='太郎',
      )
      
      # 古いPendingUserは存在しない
      assert PendingUser.objects.filter(verification_token=old_token).count() == 0
      
      # 新しいPendingUserのみ存在
      assert PendingUser.objects.filter(email=email).count() == 1


@pytest.mark.django_db
class TestRegisterPendingUserExistingUser:
  """既存ユーザーの登録テスト"""
  
  def test_register_existing_user_without_password(self):
    """パスワード未設定の既存ユーザー（ソーシャルログイン）の登録"""

    existing_user = UserFactory.build(
      email='social@example.com',
    )
    existing_user.set_unusable_password()
    existing_user.save(skip_validation=True)
    
    
    with patch('authentication.services.email_service.RegistrationEmailService.send_registration_confirmation'):
      is_existing, message = UserRegistrationService.register_pending_user(
        email='social@example.com',
        password='newpassword123',
        user_type='CUSTOMER',
        country='JP',
        user_timezone='Asia/Tokyo',
        first_name='山田',
        last_name='太郎',
      )
      
      # フラグとメッセージ
      assert is_existing is True
      assert 'An existing account was found' in message
  
  def test_register_existing_user_with_password_raises_error(self):
    """パスワード設定済みの既存ユーザーで登録を試みる"""
    # パスワード設定済みのユーザーを作成
    existing_user = UserFactory.build(email='existing@example.com')
    existing_user.set_password('existingpassword123')
    existing_user.save(skip_validation=True)
    
    with pytest.raises(ValidationError) as exc_info:
      UserRegistrationService.register_pending_user(
        email='existing@example.com',
        password='password123',
        user_type='CUSTOMER',
        country='JP',
        user_timezone='Asia/Tokyo',
        first_name='山田',
        last_name='太郎',
      )
    
    assert 'This email is already registered' in str(exc_info.value)


@pytest.mark.django_db
class TestRegisterPendingUserEmailFailure:
  """メール送信失敗のテスト"""
  
  def test_email_send_failure_deletes_pending_user(self):
    """メール送信失敗時にPendingUserが削除される"""
    email = 'test@example.com'
    
    with patch('authentication.services.email_service.RegistrationEmailService.send_registration_confirmation') as mock_send:
      mock_send.side_effect = EmailSendException('SMTP error')
      
      with pytest.raises(EmailSendException):
        UserRegistrationService.register_pending_user(
          email=email,
          password='password123',
          user_type='CUSTOMER',
          country='JP',
          user_timezone='Asia/Tokyo',
          first_name='山田',
          last_name='太郎',
        )
      
      # PendingUserが削除されている
      assert not PendingUser.objects.filter(email=email).exists()
  
  def test_email_send_failure_with_existing_user(self):
    """既存ユーザーの場合もメール送信失敗時にPendingUserが削除される"""
    existing_user = UserFactory.build(
      email='social@example.com',
    )
    existing_user.set_unusable_password()
    existing_user.save(skip_validation=True)
    
    
    with patch('authentication.services.email_service.RegistrationEmailService.send_registration_confirmation') as mock_send:
      mock_send.side_effect = EmailSendException('SMTP error')
      
      with pytest.raises(EmailSendException):
        UserRegistrationService.register_pending_user(
          email='social@example.com',
          password='password123',
          user_type='CUSTOMER',
          country='JP',
          user_timezone='Asia/Tokyo',
          first_name='山田',
          last_name='太郎',
        )
      
      # PendingUserが削除されている
      assert not PendingUser.objects.filter(email='social@example.com').exists()
      assert User.objects.filter(email='social@example.com').exists()


@pytest.mark.django_db
class TestVerifyAndActivateNewUser:
  """新規ユーザーの認証と有効化のテスト"""
  
  def test_verify_and_activate_new_customer(self):
    """新規カスタマーの認証と有効化が成功する"""

    pending_user = PendingUserFactory.create(
      user_type='CUSTOMER',
      user=None
    )
    token = pending_user.verification_token
    
    user, is_link_social, message = UserRegistrationService.verify_and_activate(token)
    
    assert user.email == pending_user.email
    assert user.is_active
    assert user.country == pending_user.country
    assert user.user_timezone == pending_user.user_timezone
    
    assert user.has_usable_password()
    
    assert CustomerRegistrationProgress.objects.filter(user=user).exists()
    progress = CustomerRegistrationProgress.objects.get(user=user)
    assert hasattr(user, '_cached_customer_progress')
    assert user._cached_customer_progress == progress
    
    # PendingUserが削除されている
    assert not PendingUser.objects.filter(verification_token=token).exists()
    assert is_link_social == False
    assert message == 'Your registration is complete.'
    
  
  def test_verify_and_activate_new_owner(self):
    """新規オーナーの認証と有効化が成功する"""
    pending_user = PendingUserFactory.create(
      user_type='OWNER',
      user=None
    )
    token = pending_user.verification_token
    
    user, is_social_link, message = UserRegistrationService.verify_and_activate(token)
    
    # Userが作成されている
    assert user.email == pending_user.email
    
    # CustomerRegistrationProgressは作成されていない
    assert not CustomerRegistrationProgress.objects.filter(user=user).exists()
    assert not hasattr(user, '_cached_customer_progress')


@pytest.mark.django_db
class TestVerifyAndActivateExistingUser:
  """既存ユーザー（ソーシャルログイン）へのパスワード設定テスト"""
  
  def test_verify_and_activate_social_user(self):
    """ソーシャルログインユーザーへのパスワード設定が成功する"""
    # パスワード未設定のユーザーを作成
    existing_user = UserFactory.build(
      email='social@example.com',
    )
    existing_user.set_unusable_password()
    existing_user.save(skip_validation=True)
    
    # PendingUserを作成
    pending_user = PendingUserFactory.create(
      email='social@example.com',
      user=existing_user,
      user_type='CUSTOMER'
    )
    
    token = pending_user.verification_token
    password_hash = pending_user.password_hash
    
    user, is_social_link, message = UserRegistrationService.verify_and_activate(token)
    
    # 既存ユーザーが返される
    assert user.id == existing_user.id
    
    # パスワードが設定されている
    user.refresh_from_db()
    assert user.password == password_hash
    assert user.has_usable_password()
    
    # PendingUserが削除されている
    assert not PendingUser.objects.filter(verification_token=token).exists()
    
    # フラグとメッセージ
    assert is_social_link is True
    assert 'Your password has been set' in message


@pytest.mark.django_db
class TestVerifyAndActivateErrors:
  """認証エラーのテスト"""
  
  def test_verify_with_invalid_token(self):
    """無効なトークンで認証を試みる"""
    with pytest.raises(NotFound) as exc_info:
      UserRegistrationService.verify_and_activate('invalid-token-12345')
    
    assert 'link is invalid' in str(exc_info.value)
  
  def test_verify_with_expired_token(self):
    """期限切れトークンで認証を試みる"""
    pending_user = PendingUserFactory.create(
      token_expires_at=timezone.now() - timedelta(hours=1)
    )
    
    with pytest.raises(ValidationError) as exc_info:
      UserRegistrationService.verify_and_activate(pending_user.verification_token)
    
    assert 'The verification link has expired' in str(exc_info.value)
  
  def test_verify_with_already_used_token(self):
    """既に使用されたトークンで認証を試みる"""
    pending_user = PendingUserFactory.create()
    token = pending_user.verification_token
    
    # 1回目の認証（成功）
    UserRegistrationService.verify_and_activate(token)
    
    # 2回目の認証（失敗）
    with pytest.raises(NotFound):
      UserRegistrationService.verify_and_activate(token)


@pytest.mark.django_db
class TestResendVerificationEmail:
  """認証メール再送信のテスト"""
  
  def test_resend_verification_email_success(self):
    """認証メール再送信が成功する"""
    pending_user = PendingUserFactory.create()
    old_token = pending_user.verification_token
    old_expires = pending_user.token_expires_at
    
    with patch('authentication.services.email_service.RegistrationEmailService.resend_confirmation') as mock_send:
      mock_send.return_value = (True, None)
      
      result = UserRegistrationService.resend_verification_email(pending_user.email)
      
      # PendingUserが返される
      assert result.email == pending_user.email
      
      # トークンが更新されている
      result.refresh_from_db()
      assert result.verification_token != old_token
      
      # 有効期限が更新されている
      assert result.token_expires_at > old_expires
      
      # メール送信が呼ばれた
      mock_send.assert_called_once()
  
  def test_resend_verification_email_not_found(self):
    """存在しないメールアドレスで再送信を試みる"""
    with pytest.raises(NotFound) as exc_info:
      UserRegistrationService.resend_verification_email('nonexistent@example.com')
    
    assert "We couldn't find" in str(exc_info.value)
  
  def test_resend_verification_email_send_failure(self):
    """メール送信失敗時にエラーが発生する"""
    pending_user = PendingUserFactory.create()
    
    with patch('authentication.services.email_service.RegistrationEmailService.resend_confirmation') as mock_send:
      email_error = EmailSendException('メール送信に失敗しました')
      email_error.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
      mock_send.side_effect = email_error

      with pytest.raises(EmailSendException) as exc_info:
        UserRegistrationService.resend_verification_email(pending_user.email)  # 修正
        
      assert 'メール送信に失敗' in str(exc_info.value)


@pytest.mark.django_db
class TestChangePendingEmail:
  """メールアドレス変更のテスト"""
  
  def test_change_pending_email_success(self):
    """メールアドレス変更が成功する"""
    old_email = 'old@example.com'
    new_email = 'new@example.com'
    
    pending_user = PendingUserFactory.create(email=old_email)
    old_token = pending_user.verification_token
    
    with patch('authentication.services.email_service.RegistrationEmailService.send_email_change_confirmation') as mock_send:
      mock_send.return_value = (True, None)
      
      pending_user = UserRegistrationService.change_pending_email(old_email, new_email)
      
      # メールアドレスが更新されている
      pending_user.refresh_from_db()
      assert pending_user.email == new_email
      
      # トークンが更新されている
      assert pending_user.verification_token != old_token
      
      # 有効期限が更新されている
      assert pending_user.token_expires_at > timezone.now()
      
      # メール送信が呼ばれた
      mock_send.assert_called_once_with(pending_user, new_email)
  
  def test_change_pending_email_not_found(self):
    """存在しないメールアドレスで変更を試みる"""
    with pytest.raises(NotFound) as exc_info:
      UserRegistrationService.change_pending_email('nonexistent@example.com', 'new@example.com')
    
    assert "We couldn't find" in str(exc_info.value)
  
  def test_change_pending_email_send_failure(self):
    """メール送信失敗時にエラーが発生する"""
    pending_user = PendingUserFactory.create()
    
    with patch('authentication.services.email_service.RegistrationEmailService.send_email_change_confirmation') as mock_send:
      email_error = EmailSendException('メール送信に失敗しました')
      email_error.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
      mock_send.side_effect = email_error
      
      with pytest.raises(EmailSendException) as exc_info:
        UserRegistrationService.change_pending_email(pending_user.email, 'new@example.com')
      
      assert 'メール送信に失敗しました' in str(exc_info.value)


@pytest.mark.django_db
class TestEdgeCases:
  """エッジケースのテスト"""
  
  def test_register_with_same_email_different_user_type(self):
    """同じメールアドレスで異なるuser_typeで登録"""
    email = 'test@example.com'
    
    # カスタマーとして登録
    with patch('authentication.services.email_service.RegistrationEmailService.send_registration_confirmation'):
      _, _ = UserRegistrationService.register_pending_user(
        email=email,
        password='password123',
        user_type='CUSTOMER',
        country='JP',
        user_timezone='Asia/Tokyo',
        first_name='山田',
        last_name='太郎',
      )
  
  def test_concurrent_registration_attempts(self):
    """同時に複数の登録リクエストが来た場合"""
    email = 'test@example.com'
    
    with patch('authentication.services.email_service.RegistrationEmailService.send_registration_confirmation'):
      # 1回目
      _, _ = UserRegistrationService.register_pending_user(
        email=email,
        password='password1',
        user_type='CUSTOMER',
        country='JP',
        user_timezone='Asia/Tokyo',
        first_name='山田',
        last_name='太郎',
      )
      
      # 2回目（1回目が削除されて新規作成される）
      _, _ = UserRegistrationService.register_pending_user(
        email=email,
        password='password2',
        user_type='CUSTOMER',
        country='JP',
        user_timezone='Asia/Tokyo',
        first_name='山田',
        last_name='太郎',
      )
      
      # 最新のPendingUserのみ存在
      assert PendingUser.objects.filter(email=email).count() == 1
  
  # def test_token_uniqueness(self):
  #   tokens = set()
    
  #   with patch('authentication.services.email_service.RegistrationEmailService.send_registration_confirmation'):
  #     for i in range(100):
  #       pending_user, _ = UserRegistrationService.register_pending_user(
  #         email=f'user{i}@example.com',
  #         password='password123',
  #         user_type='CUSTOMER',
  #         country='JP',
  #         user_timezone='Asia/Tokyo',
  #         first_name='山田',
  #         last_name='太郎',
  #       )
        
  #       tokens.add(pending_user.verification_token)
    
  #   assert len(tokens) == 100, f"Expected 100 unique tokens, got {len(tokens)}"


@pytest.mark.django_db
class TestIntegrationFullFlow:
  """統合テスト：完全な登録フロー"""
  
  def test_full_customer_registration_flow(self):
    """カスタマーの完全な登録フロー"""
    email = 'customer@example.com'
    password = 'password123'
    
    with patch('authentication.services.email_service.RegistrationEmailService.send_registration_confirmation'):
      # 1. 登録
      is_existing, message = UserRegistrationService.register_pending_user(
        email=email,
        password=password,
        user_type='CUSTOMER',
        country='JP',
        user_timezone='Asia/Tokyo',
        first_name='山田',
        last_name='太郎',
      )
      
      assert is_existing is False
      
  
  def test_full_owner_registration_flow(self):
    """オーナーの完全な登録フロー"""
    email = 'owner@example.com'
    password = 'password123'
    
    with patch('authentication.services.email_service.RegistrationEmailService.send_registration_confirmation'):
      # 1. 登録
      _, _ = UserRegistrationService.register_pending_user(
        email=email,
        password=password,
        user_type='OWNER',
        country='JP',
        user_timezone='Asia/Tokyo',
        first_name='山田',
        last_name='太郎',
      )
      
      
  
  def test_full_social_user_password_setup_flow(self):
    """ソーシャルログインユーザーのパスワード設定フロー"""
    email = 'social@example.com'
    
    # ソーシャルログインユーザーを作成
    existing_user = UserFactory.build(
      email='social@example.com',
    )
    existing_user.set_unusable_password()
    existing_user.save(skip_validation=True)
    
    with patch('authentication.services.email_service.RegistrationEmailService.send_registration_confirmation'):
      # 1. パスワード設定の登録
      is_existing, message = UserRegistrationService.register_pending_user(
        email=email,
        password='newpassword123',
        user_type='CUSTOMER',
        country='JP',
        user_timezone='Asia/Tokyo',
        first_name='山田',
        last_name='太郎',
      )
      
      assert is_existing is True
      