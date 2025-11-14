import pytest
from django.core.exceptions import ValidationError
from core.models import User
from core.services.social_login_service import SocialLoginService
from core.services.user_registration_service import UserRegistrationService
from tests.factories.core import UserFactory


@pytest.mark.django_db
class TestMultipleSocialAccountLinking:
  """複数ソーシャルアカウント連携のテスト"""
  
  def test_7_1_1_google_then_line_addition(self, mock_social_apis):
    """7.1.1: Google→LINE追加"""
    user, _, _ = SocialLoginService.get_or_create_user(
      user_type='CUSTOMER',
      access_token='valid_google_token',
      provider='google',
      session_token=None,
      id_token=None
    )
    
    google_user_id = user.google_user_id
    email = user.email
    
    user, _, message = SocialLoginService.get_or_create_user(
      user_type='CUSTOMER',
      access_token='valid_line_token',
      provider='line',
      session_token=None,
      id_token='valid_id_token'
    )
    
    assert user.google_user_id == google_user_id
    assert user.line_user_id == 'U1234567890abcdef'
    assert user.auth_provider == 'line'  # 最後に使用したプロバイダー
    assert 'Lineアカウントを追加しました' in message
  
  def test_7_1_2_line_then_google_addition(self, mock_social_apis):
    """7.1.2: LINE→Google追加"""
    # LINE初回サインアップ
    user, _, _ = SocialLoginService.get_or_create_user(
      user_type='CUSTOMER',
      access_token='valid_line_token',
      provider='line',
      session_token=None,
      id_token='valid_id_token'
    )
    
    line_user_id = user.line_user_id
    
    # Google追加
    user, _, message = SocialLoginService.get_or_create_user(
      user_type='CUSTOMER',
      access_token='valid_google_token',
      provider='google',
      session_token=None,
      id_token=None
    )
    
    assert user.line_user_id == line_user_id
    assert user.google_user_id == '123456789'
    assert user.auth_provider == 'google'
    assert 'Googleアカウントを追加しました' in message
  
  def test_7_1_3_email_then_google_addition(self, mock_google_api):
    """7.1.3: email→Google追加"""
    # Email登録
    email_user = UserFactory(
      email='test@example.com',
      auth_provider='email',
      google_user_id=None
    )
    
    # Google追加
    user, _, message = SocialLoginService.get_or_create_user(
      user_type='CUSTOMER',
      access_token='valid_google_token',
      provider='google',
      session_token=None,
      id_token=None
    )
    
    assert user.id == email_user.id
    assert user.google_user_id == '123456789'
    assert 'Googleアカウントを追加しました' in message
  
  def test_7_1_4_email_then_line_addition(self, mock_line_api):
    """7.1.4: email→LINE追加"""
    # Email登録
    email_user = UserFactory(
      email='test@example.com',
      auth_provider='email',
      line_user_id=None
    )
    
    # LINE追加
    user, _, message = SocialLoginService.get_or_create_user(
      user_type='CUSTOMER',
      access_token='valid_line_token',
      provider='line',
      session_token=None,
      id_token='valid_id_token'
    )
    
    assert user.id == email_user.id
    assert user.line_user_id == 'U1234567890abcdef'
    assert 'Lineアカウントを追加しました' in message


@pytest.mark.django_db
class TestMultipleSocialAccountLogin:
  """複数プロバイダーでのログインテスト"""
  
  def test_7_2_1_login_with_both_google_and_line(self, mock_social_apis):
    """7.2.1: Google/LINE両方でログイン可能"""
    # Google/LINE両方登録済みユーザー作成
    user = UserFactory(
      email='test@example.com',
      google_user_id='123456789',
      line_user_id='U1234567890abcdef',
      auth_provider='google'
    )
    
    # Googleでログイン
    google_user, _, google_msg = SocialLoginService.get_or_create_user(
      user_type='CUSTOMER',
      access_token='valid_google_token',
      provider='google',
      session_token=None,
      id_token=None
    )
    
    assert google_user.id == user.id
    assert 'Googleアカウントでログインしました' in google_msg
    
    # LINEでログイン
    line_user, _, line_msg = SocialLoginService.get_or_create_user(
      user_type='CUSTOMER',
      access_token='valid_line_token',
      provider='line',
      session_token=None,
      id_token='valid_id_token'
    )
    
    assert line_user.id == user.id
    assert 'Lineアカウントでログインしました' in line_msg
  
  def test_7_2_2_last_used_provider(self, mock_social_apis):
    """7.2.2: 最後に使用したプロバイダー"""
    # Google/LINE両方登録済み
    user = UserFactory(
      email='test@example.com',
      google_user_id='123456789',
      line_user_id='U1234567890abcdef',
      auth_provider='line'
    )
    
    # LINEでログイン
    line_user, _, _ = SocialLoginService.get_or_create_user(
      user_type='CUSTOMER',
      access_token='valid_line_token',
      provider='line',
      session_token=None,
      id_token='valid_id_token'
    )
    
    assert line_user.auth_provider == 'line'
    
    # Googleでログイン
    google_user, _, _ = SocialLoginService.get_or_create_user(
      user_type='CUSTOMER',
      access_token='valid_google_token',
      provider='google',
      session_token=None,
      id_token=None
    )
    
    google_user.refresh_from_db()
    assert google_user.auth_provider == 'google'  # 更新されている


@pytest.mark.django_db
class TestMultipleSocialAccountEdgeCases:
  """複数連携のエッジケース"""
  
  def test_7_1_5_google_user_can_add_email_password(self):
    """7.1.5: Googleユーザー→email/password追加可能"""
    
    google_user = UserFactory(
      email='test@example.com',
      google_user_id='google_123',
      auth_provider='google',
      is_active=True,
      password=''
    )
    google_user.set_unusable_password()
    google_user.save()
    
    assert google_user.google_user_id == 'google_123'
    
    user, _, message = UserRegistrationService.register_user(
      session_token=None,
      user_type='CUSTOMER',
      data={
        'email': 'test@example.com',
        'password': 'newpassword123',
        'password_confirm': 'newpassword123',
      },
    )
    
    assert user.check_password('newpassword123')
    assert user.google_user_id == 'google_123'
    assert user.auth_provider == 'email'
    assert 'メール認証' in message


  def test_7_1_6_google_user_cannot_add_another_google(self, mock_google_api):
    """7.1.6: Googleユーザー→別のGoogle追加不可"""
    google_user = UserFactory(
      email='test@example.com',
      google_user_id='google_123',
      auth_provider='google',
      is_active=True
    )
    
    with pytest.raises(ValidationError, match='既に別の'):
      SocialLoginService.get_or_create_user(
        user_type='CUSTOMER',
        access_token='another_google_token',
        provider='google',
      )
