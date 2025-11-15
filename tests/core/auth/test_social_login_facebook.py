import pytest
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from users.models import User
from authentication.services.social_login_service import SocialLoginService
from ...factories import UserFactory, StaffInvitationFactory


@pytest.mark.django_db
class TestFacebookCustomerSignup:
  """CUSTOMER Facebook新規登録のテスト"""
  
  def test_6_1_1_facebook_first_signup(self, mock_facebook_api):
    """6.1.1: Facebook初回サインアップ"""
    user, refresh, message = SocialLoginService.get_or_create_user(
      user_type='CUSTOMER',
      access_token='valid_facebook_token',
      provider='facebook',
      session_token=None,
      id_token=None
    )
    
    assert user.email == 'test@example.com'
    assert user.facebook_user_id == 'fb123456789'
    assert user.user_type == 'CUSTOMER'
    assert user.is_email_verified is True
    assert user.auth_provider == 'facebook'
    assert refresh is not None
    assert 'Facebookでアカウントを作成しました' in message
  
  
  def test_6_1_3_facebook_signup_email_from_api(self, mock_facebook_api):
    """6.1.3: Facebookサインアップ（email取得）"""
    user, _, _ = SocialLoginService.get_or_create_user(
      user_type='CUSTOMER',
      access_token='valid_facebook_token',
      provider='facebook',
      session_token=None,
      id_token=None
    )
    
    assert user.email == 'test@example.com'
  
  def test_6_1_4_facebook_signup_picture_url(self, mock_facebook_api):
    """6.1.4: Facebookサインアップ（picture）"""
    user, _, _ = SocialLoginService.get_or_create_user(
      user_type='CUSTOMER',
      access_token='valid_facebook_token',
      provider='facebook',
      session_token=None,
      id_token=None
    )
    
    assert user.profile_image_url == 'https://example.com/photo.jpg'
  
  def test_6_1_5_facebook_user_id_from_api(self, mock_facebook_api):
    """6.1.5: Facebook userId取得"""
    user, _, _ = SocialLoginService.get_or_create_user(
      user_type='CUSTOMER',
      access_token='valid_facebook_token',
      provider='facebook',
      session_token=None,
      id_token=None
    )
    
    assert user.facebook_user_id == 'fb123456789'
  
  def test_6_1_6_invalid_facebook_token(self, mock_line_api_error_401):
    """6.1.6: 無効なFacebookアクセストークン"""
    with pytest.raises(ValidationError, match='Facebookトークンが無効です'):
      SocialLoginService.get_or_create_user(
        user_type='CUSTOMER',
        access_token='invalid_token',
        provider='facebook',
        session_token=None,
        id_token=None
      )
  
  def test_6_1_7_facebook_no_email(self, mock_facebook_api_no_email):
    """6.1.7: Facebookからemailなし"""
    with pytest.raises(ValidationError):
      SocialLoginService.get_or_create_user(
        user_type='CUSTOMER',
        access_token='valid_facebook_token',
        provider='facebook',
        session_token=None,
        id_token=None
      )


@pytest.mark.django_db
class TestFacebookExistingUser:
  """CUSTOMER Facebook既存ユーザーのテスト"""
  
  def test_6_2_1_facebook_re_login(self, mock_facebook_api):
    """6.2.1: Facebook再ログイン"""
    existing_user = UserFactory(
      email='test@example.com',
      facebook_user_id='fb123456789',
      auth_provider='facebook'
    )
    
    user, refresh, message = SocialLoginService.get_or_create_user(
      user_type='CUSTOMER',
      access_token='valid_facebook_token',
      provider='facebook',
      session_token=None,
      id_token=None
    )
    
    assert user.id == existing_user.id
    assert refresh is not None
    assert 'Facebookアカウントでログインしました' in message
  
  def test_6_2_2_add_facebook_to_email_user(self, mock_facebook_api):
    """6.2.2: 既存メール（email登録）にFacebookアカウント追加"""
    existing_user = UserFactory(
      email='test@example.com',
      auth_provider='email',
      facebook_user_id=None
    )
    
    user, refresh, message = SocialLoginService.get_or_create_user(
      user_type='CUSTOMER',
      access_token='valid_facebook_token',
      provider='facebook',
      session_token=None,
      id_token=None
    )
    
    assert user.id == existing_user.id
    assert user.facebook_user_id == 'fb123456789'
    assert user.auth_provider == 'facebook'
    assert 'Facebookアカウントを追加しました' in message
  
  def test_6_2_3_add_facebook_to_google_user(self, mock_facebook_api):
    """6.2.3: 既存メール（Google登録）にFacebook追加"""
    existing_user = UserFactory(
      email='test@example.com',
      auth_provider='google',
      google_user_id='123456789',
      facebook_user_id=None
    )
    
    user, _, _ = SocialLoginService.get_or_create_user(
      user_type='CUSTOMER',
      access_token='valid_facebook_token',
      provider='facebook',
      session_token=None,
      id_token=None
    )
    
    assert user.id == existing_user.id
    assert user.facebook_user_id == 'fb123456789'
    assert user.google_user_id == '123456789'  # そのまま
  
  def test_6_2_4_facebook_login_email_changed(self, mock_facebook_api):
    """6.2.4: Facebookログイン時のメール変更"""
    existing_user = UserFactory(
      email='old@example.com',
      facebook_user_id='fb123456789',
      auth_provider='facebook'
    )
    
    user, _, _ = SocialLoginService.get_or_create_user(
      user_type='CUSTOMER',
      access_token='valid_facebook_token',
      provider='facebook',
      session_token=None,
      id_token=None
    )
    
    assert user.id == existing_user.id
    assert user.email == 'test@example.com'  # 更新されている


@pytest.mark.django_db
class TestFacebookOwnerLogin:
  """OWNER Facebookログインのテスト"""
  
  def test_6_3_1_owner_facebook_first_signup(self, mock_facebook_api):
    """6.3.1: OWNER Facebook初回サインアップ"""
    user, refresh, message = SocialLoginService.get_or_create_user(
      user_type='OWNER',
      access_token='valid_facebook_token',
      provider='facebook',
      session_token=None,
      id_token=None
    )
    
    assert user.user_type == 'OWNER'
    assert user.facebook_user_id == 'fb123456789'
  
  def test_6_3_2_owner_facebook_re_login(self, mock_facebook_api):
    """6.3.2: OWNER Facebook再ログイン"""
    existing_owner = UserFactory(
      user_type='OWNER',
      email='test@example.com',
      facebook_user_id='fb123456789',
      auth_provider='facebook'
    )
    
    user, refresh, _ = SocialLoginService.get_or_create_user(
      user_type='OWNER',
      access_token='valid_facebook_token',
      provider='facebook',
      session_token=None,
      id_token=None
    )
    
    assert user.id == existing_owner.id
    assert refresh is not None


@pytest.mark.django_db
class TestFacebookStaffWithInvitation:
  """STAFF Facebook招待アクティベーションのテスト"""
  
  def test_6_4_1_facebook_invitation_activation(self, mock_facebook_api):
    """6.4.1: Facebook招待アクティベート"""
    user = UserFactory(
      email='test@example.com',
      user_type='STAFF',
      is_active=False,
      facebook_user_id=None,
      auth_provider='email'
    )
    invitation = StaffInvitationFactory(
      email='test@example.com',
      user=user
    )
    
    session_token = 'test_session_token'
    
    cache_key = f'invitation_session:{session_token}'
    cache.set(cache_key, {
      'invitation_id': str(invitation.id),
      'invitation_token': invitation.token,
      'email': invitation.email,
    }, timeout=900)
    
    user, refresh, message = SocialLoginService.get_or_create_user(
      user_type='STAFF',
      access_token='valid_facebook_token',
      provider='facebook',
      session_token=session_token,
      id_token=None
    )
    
    assert user.is_active is True
    assert user.facebook_user_id == 'fb123456789'
    assert user.auth_provider == 'facebook'
  
  
  def test_6_4_3_activation_invitation_and_progress(self, mock_facebook_api):
    """6.4.3: アクティベート後の招待・プログレス"""
    user = UserFactory(
      email='test@example.com',
      user_type='STAFF',
      is_active=False,
      facebook_user_id=None,
      auth_provider='email'
    )
    invitation = StaffInvitationFactory(
      email='test@example.com',
      user=user
    )
    session_token = 'test_session_token'
    
    cache_key = f'invitation_session:{session_token}'
    cache.set(cache_key, {
      'invitation_id': str(invitation.id),
      'invitation_token': invitation.token,
      'email': invitation.email,
    }, timeout=900)
    
    user, _, _ = SocialLoginService.get_or_create_user(
      user_type='STAFF',
      access_token='valid_facebook_token',
      provider='facebook',
      session_token=session_token,
      id_token=None
    )
    
    invitation.refresh_from_db()
    assert invitation.is_used is True
    
    progress = user.staff_progress
    assert progress.step == 'profile'
  
  def test_6_4_4_invalid_facebook_token_with_invitation(self, mock_line_api_error_401):
    """6.4.4: 無効なFacebookトークン（招待あり）"""
    invitation = StaffInvitationFactory(email='test@example.com')
    session_token = 'test_session_token'
    
    cache_key = f'invitation_session:{session_token}'
    cache.set(cache_key, {
      'invitation_id': str(invitation.id),
      'invitation_token': invitation.token,
      'email': invitation.email,
    }, timeout=900)
    
    with pytest.raises(ValidationError, match='Facebookトークンが無効です'):
      SocialLoginService.get_or_create_user(
        user_type='STAFF',
        access_token='invalid_token',
        provider='facebook',
        session_token=session_token,
        id_token=None
      )