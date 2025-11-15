import pytest
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from users.models import User
from authentication.services.social_login_service import SocialLoginService
from ...factories import UserFactory, StaffInvitationFactory


@pytest.mark.django_db
class TestLineCustomerSignup:
  """CUSTOMER LINE新規登録のテスト"""
  
  def test_5_1_1_line_first_signup(self, mock_line_api):
    """5.1.1: LINE初回サインアップ"""
    user, refresh, message = SocialLoginService.get_or_create_user(
      user_type='CUSTOMER',
      access_token='valid_line_token',
      provider='line',
      session_token=None,
      id_token='valid_id_token'
    )
    
    assert user.email == 'test@example.com'
    assert user.line_user_id == 'U1234567890abcdef'
    assert user.user_type == 'CUSTOMER'
    assert user.is_email_verified is True
    assert user.auth_provider == 'line'
    assert refresh is not None
    assert 'Lineでアカウントを作成しました' in message
  
  
  def test_5_1_3_line_signup_email_from_id_token(self, mock_line_api):
    """5.1.3: LINEサインアップ（email取得）"""
    user, _, _ = SocialLoginService.get_or_create_user(
      user_type='CUSTOMER',
      access_token='valid_line_token',
      provider='line',
      session_token=None,
      id_token='valid_id_token'
    )
    
    assert user.email == 'test@example.com'
  
  def test_5_1_4_line_signup_picture_url(self, mock_line_api):
    """5.1.4: LINEサインアップ（pictureUrl）"""
    user, _, _ = SocialLoginService.get_or_create_user(
      user_type='CUSTOMER',
      access_token='valid_line_token',
      provider='line',
      session_token=None,
      id_token='valid_id_token'
    )
    
    assert user.profile_image_url == 'https://example.com/photo.jpg'
  
  def test_5_1_5_line_user_id_priority(self, mock_line_api):
    """5.1.5: LINE userId優先"""
    user, _, _ = SocialLoginService.get_or_create_user(
      user_type='CUSTOMER',
      access_token='valid_line_token',
      provider='line',
      session_token=None,
      id_token='valid_id_token'
    )
    
    # id_token.sub を優先
    assert user.line_user_id == 'U1234567890abcdef'
  
  def test_5_1_6_invalid_line_token(self, mock_line_api_error_401):
    """5.1.6: 無効なLINEアクセストークン"""
    with pytest.raises(ValidationError, match='LINEトークンが無効です'):
      SocialLoginService.get_or_create_user(
        user_type='CUSTOMER',
        access_token='invalid_token',
        provider='line',
        session_token=None,
        id_token='valid_id_token'
      )
  
  def test_5_1_7_invalid_line_id_token(self, mock_line_api_invalid_id_token):
    """5.1.7: 無効なLINE IDトークン"""
    with pytest.raises(ValidationError, match='LINEトークンが無効です'):
      SocialLoginService.get_or_create_user(
        user_type='CUSTOMER',
        access_token='valid_line_token',
        provider='line',
        session_token=None,
        id_token='invalid_id_token'
      )
  
  def test_5_1_8_line_no_email(self, mock_line_api_no_email):
    """5.1.8: LINEからemailなし"""
    with pytest.raises(ValidationError):
      SocialLoginService.get_or_create_user(
        user_type='CUSTOMER',
        access_token='valid_line_token',
        provider='line',
        session_token=None,
        id_token='id_token_no_email'
      )
  
  def test_5_1_10_line_no_id_token(self, mock_line_api):
    """5.1.10: id_tokenなし"""
    with pytest.raises(ValidationError):
      SocialLoginService.get_or_create_user(
        user_type='CUSTOMER',
        access_token='valid_line_token',
        provider='line',
        session_token=None,
        id_token=None
      )


@pytest.mark.django_db
class TestLineExistingUser:
  """CUSTOMER LINE既存ユーザーのテスト"""
  
  def test_5_2_1_line_re_login(self, mock_line_api):
    """5.2.1: LINE再ログイン"""
    existing_user = UserFactory(
      email='test@example.com',
      line_user_id='U1234567890abcdef',
      auth_provider='line'
    )
    
    user, refresh, message = SocialLoginService.get_or_create_user(
      user_type='CUSTOMER',
      access_token='valid_line_token',
      provider='line',
      session_token=None,
      id_token='valid_id_token'
    )
    
    assert user.id == existing_user.id
    assert refresh is not None
    assert 'Lineアカウントでログインしました' in message
  
  def test_5_2_2_add_line_to_email_user(self, mock_line_api):
    """5.2.2: 既存メール（email登録）にLINEアカウント追加"""
    existing_user = UserFactory(
      email='test@example.com',
      auth_provider='email',
      line_user_id=None
    )
    
    user, refresh, message = SocialLoginService.get_or_create_user(
      user_type='CUSTOMER',
      access_token='valid_line_token',
      provider='line',
      session_token=None,
      id_token='valid_id_token'
    )
    
    assert user.id == existing_user.id
    assert user.line_user_id == 'U1234567890abcdef'
    assert user.auth_provider == 'line'
    assert 'Lineアカウントを追加しました' in message
  
  def test_5_2_3_add_line_to_google_user(self, mock_line_api):
    """5.2.3: 既存メール（Google登録）にLINE追加"""
    existing_user = UserFactory(
      email='test@example.com',
      auth_provider='google',
      google_user_id='123456789',
      line_user_id=None
    )
    
    user, _, _ = SocialLoginService.get_or_create_user(
      user_type='CUSTOMER',
      access_token='valid_line_token',
      provider='line',
      session_token=None,
      id_token='valid_id_token'
    )
    
    assert user.id == existing_user.id
    assert user.line_user_id == 'U1234567890abcdef'
    assert user.google_user_id == '123456789'  # そのまま
  
  def test_5_2_4_line_login_email_changed(self, mock_line_api):
    """5.2.4: LINEログイン時のメール変更"""
    existing_user = UserFactory(
      email='old@example.com',
      line_user_id='U1234567890abcdef',
      auth_provider='line'
    )
    
    user, _, _ = SocialLoginService.get_or_create_user(
      user_type='CUSTOMER',
      access_token='valid_line_token',
      provider='line',
      session_token=None,
      id_token='valid_id_token'
    )
    
    assert user.id == existing_user.id
    assert user.email == 'test@example.com'  # 更新されている


@pytest.mark.django_db
class TestLineOwnerLogin:
  """OWNER LINEログインのテスト"""
  
  def test_5_3_1_owner_line_first_signup(self, mock_line_api):
    """5.3.1: OWNER LINE初回サインアップ"""
    user, refresh, message = SocialLoginService.get_or_create_user(
      user_type='OWNER',
      access_token='valid_line_token',
      provider='line',
      session_token=None,
      id_token='valid_id_token'
    )
    
    assert user.user_type == 'OWNER'
    assert user.line_user_id == 'U1234567890abcdef'
  
  def test_5_3_2_owner_line_re_login(self, mock_line_api):
    """5.3.2: OWNER LINE再ログイン"""
    existing_owner = UserFactory(
      user_type='OWNER',
      email='test@example.com',
      line_user_id='U1234567890abcdef',
      auth_provider='line'
    )
    
    user, refresh, _ = SocialLoginService.get_or_create_user(
      user_type='OWNER',
      access_token='valid_line_token',
      provider='line',
      session_token=None,
      id_token='valid_id_token'
    )
    
    assert user.id == existing_owner.id
    assert refresh is not None


@pytest.mark.django_db
class TestLineStaffWithInvitation:
  """STAFF LINE招待アクティベーションのテスト"""
  
  def test_5_4_1_line_invitation_activation(self, mock_line_api):
    """5.4.1: LINE招待アクティベート"""
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
      access_token='valid_line_token',
      provider='line',
      session_token=session_token,
      id_token='valid_id_token'
    )
    
    assert user.is_active is True
    assert user.line_user_id == 'U1234567890abcdef'
    assert user.auth_provider == 'line'
  
  
  def test_5_4_3_activation_invitation_and_progress(self, mock_line_api):
    """5.4.3: アクティベート後の招待・プログレス"""
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
      access_token='valid_line_token',
      provider='line',
      session_token=session_token,
      id_token='valid_id_token'
    )
    
    invitation.refresh_from_db()
    assert invitation.is_used is True
    
    progress = user.staff_progress
    assert progress.step == 'profile'
  
  def test_5_4_4_invalid_line_token_with_invitation(self, mock_line_api_error_401):
    """5.4.4: 無効なLINEトークン（招待あり）"""
    invitation = StaffInvitationFactory(email='test@example.com')
    session_token = 'test_session_token'
    
    cache_key = f'invitation_session:{session_token}'
    cache.set(cache_key, {
      'invitation_id': str(invitation.id),
      'invitation_token': invitation.token,
      'email': invitation.email,
    }, timeout=900)
    
    with pytest.raises(ValidationError, match='LINEトークンが無効です'):
      SocialLoginService.get_or_create_user(
        user_type='STAFF',
        access_token='invalid_token',
        provider='line',
        session_token=session_token,
        id_token='valid_id_token'
      )
  
  def test_5_4_5_no_id_token_with_invitation(self, mock_line_api):
    """5.4.5: id_tokenなし（招待あり）"""
    invitation = StaffInvitationFactory(email='test@example.com')
    session_token = 'test_session_token'
    
    cache_key = f'invitation_session:{session_token}'
    cache.set(cache_key, {
      'invitation_id': str(invitation.id),
      'invitation_token': invitation.token,
      'email': invitation.email,
    }, timeout=900)
    
    with pytest.raises(ValidationError):
      SocialLoginService.get_or_create_user(
        user_type='STAFF',
        access_token='valid_line_token',
        provider='line',
        session_token=session_token,
        id_token=None
      )