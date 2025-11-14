import pytest
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from core.models import User
from core.services.social_login_service import SocialLoginService
from ...factories import UserFactory, StaffInvitationFactory


@pytest.mark.django_db
class TestGoogleCustomerSignup:
  """CUSTOMER Google新規登録のテスト"""
  
  def test_4_1_1_google_first_signup(self, mock_google_api):
    """4.1.1: Google初回サインアップ"""
    user, refresh, message = SocialLoginService.get_or_create_user(
      user_type='CUSTOMER',
      access_token='valid_google_token',
      provider='google',
      session_token=None,
      id_token=None
    )
    
    assert user.email == 'test@example.com'
    assert user.google_user_id == '123456789'
    assert user.user_type == 'CUSTOMER'
    assert user.is_email_verified is True
    assert user.is_active is True
    assert user.auth_provider == 'google'
    assert refresh is not None
    assert 'Googleでアカウントを作成しました' in message
  
  def test_4_1_2_google_signup_all_info(self, mock_google_api, query_counter):
    """4.1.2: Googleサインアップ（全情報取得）"""


    with query_counter as qc:
      user, _, _ = SocialLoginService.get_or_create_user(
        user_type='CUSTOMER',
        access_token='valid_google_token',
        provider='google',
        session_token=None,
        id_token=None
      )

    assert hasattr(user, '_cached_customer_progress')
    assert user._cached_customer_progress.step == 'detail'
    
    from core.serializers import UserSerializer
    with query_counter as qc2:
      user_serializer = UserSerializer(user)
      serialized_data = user_serializer.data
    qc2.assert_max_queries(0, "Serialization時はクエリ発行なし")
    
    assert serialized_data['progress']['step'] == 'detail'  
    assert user.first_name == '太郎'
    assert user.last_name == '山田'
    assert user.email == 'test@example.com'
    assert user.profile_image_url == 'https://example.com/photo.jpg'
    qc.assert_max_queries(6)
  
  def test_4_1_3_google_signup_no_name(self, mock_google_api_no_name):
    """4.1.3: Googleサインアップ（名前なし）"""
    user, _, _ = SocialLoginService.get_or_create_user(
      user_type='CUSTOMER',
      access_token='valid_google_token',
      provider='google',
      session_token=None,
      id_token=None
    )
    
    assert user.email == 'test@example.com'
    assert user.first_name == ''
    assert user.last_name == ''
  
  def test_4_1_4_google_signup_no_picture(self, mock_google_api_no_picture):
    """4.1.4: Googleサインアップ（pictureなし）"""
    user, _, _ = SocialLoginService.get_or_create_user(
      user_type='CUSTOMER',
      access_token='valid_google_token',
      provider='google',
      session_token=None,
      id_token=None
    )
    
    assert user.email == 'test@example.com'
    assert user.profile_image_url == ''
  
  def test_4_1_5_invalid_google_token(self, mock_google_api_error_401):
    """4.1.5: 無効なGoogleアクセストークン"""
    with pytest.raises(ValidationError, match='Googleトークンが無効です'):
      SocialLoginService.get_or_create_user(
        user_type='CUSTOMER',
        access_token='invalid_token',
        provider='google',
        session_token=None,
        id_token=None
      )
  
  def test_4_1_6_google_api_error_401(self, mock_google_api_error_401):
    """4.1.6: GoogleAPIエラー（401）"""
    with pytest.raises(ValidationError, match='Googleトークンが無効です'):
      SocialLoginService.get_or_create_user(
        user_type='CUSTOMER',
        access_token='token',
        provider='google',
        session_token=None,
        id_token=None
      )
  
  def test_4_1_7_google_api_error_403(self, mock_google_api_error_403):
    """4.1.7: GoogleAPIエラー（403）"""
    with pytest.raises(ValidationError, match='Googleトークンが無効です'):
      SocialLoginService.get_or_create_user(
        user_type='CUSTOMER',
        access_token='token',
        provider='google',
        session_token=None,
        id_token=None
      )
  
  def test_4_1_8_google_api_error_500(self, mock_google_api_error_500):
    """4.1.8: GoogleAPIエラー（500）"""
    with pytest.raises(ValidationError, match='Googleトークンが無効です'):
      SocialLoginService.get_or_create_user(
        user_type='CUSTOMER',
        access_token='token',
        provider='google',
        session_token=None,
        id_token=None
      )
  
  def test_4_1_9_google_no_email(self, mock_google_api_no_email):
    """4.1.9: Googleからemailなし"""
    with pytest.raises(ValidationError):
      SocialLoginService.get_or_create_user(
        user_type='CUSTOMER',
        access_token='token',
        provider='google',
        session_token=None,
        id_token=None
      )


@pytest.mark.django_db
class TestGoogleExistingUserBySocialId:
  """CUSTOMER Google既存ユーザー（ソーシャルID）のテスト"""
  
  def test_4_2_1_google_re_login(self, mock_google_api):
    """4.2.1: Google再ログイン"""
    # 既存ユーザー作成
    existing_user = UserFactory(
      email='test@example.com',
      google_user_id='123456789',
      auth_provider='google'
    )
    
    user, refresh, message = SocialLoginService.get_or_create_user(
      user_type='CUSTOMER',
      access_token='valid_google_token',
      provider='google',
      session_token=None,
      id_token=None
    )
    
    assert user.id == existing_user.id
    assert refresh is not None
    assert 'Googleアカウントでログインしました' in message
  
  def test_4_2_2_google_login_email_changed(self, mock_google_api):
    """4.2.2: Googleログイン時のメール変更"""
    # 既存ユーザー（異なるメール）
    existing_user = UserFactory(
      email='old@example.com',
      google_user_id='123456789',
      auth_provider='google'
    )
    
    user, _, _ = SocialLoginService.get_or_create_user(
      user_type='CUSTOMER',
      access_token='valid_google_token',
      provider='google',
      session_token=None,
      id_token=None
    )
    
    assert user.id == existing_user.id
    assert user.email == 'test@example.com'  # 更新されている
  
  def test_4_2_3_google_login_other_fields_unchanged(self, mock_google_api):
    """4.2.3: メール変更時の他フィールド"""
    existing_user = UserFactory(
      email='old@example.com',
      google_user_id='123456789',
      first_name='既存',
      last_name='ユーザー',
      auth_provider='google'
    )
    
    user, _, _ = SocialLoginService.get_or_create_user(
      user_type='CUSTOMER',
      access_token='valid_google_token',
      provider='google',
      session_token=None,
      id_token=None
    )
    
    # 名前は更新されない
    assert user.first_name == '既存'
    assert user.last_name == 'ユーザー'
    # メールのみ更新
    assert user.email == 'test@example.com'


@pytest.mark.django_db
class TestGoogleExistingUserByEmail:
  """CUSTOMER Google既存ユーザー（メールアドレス）のテスト"""
  
  def test_4_3_1_add_google_to_email_user(self, mock_google_api):
    """4.3.1: 既存メール（email登録）にGoogleアカウント追加"""
    existing_user = UserFactory(
      email='test@example.com',
      auth_provider='email',
      google_user_id=None
    )
    
    user, refresh, message = SocialLoginService.get_or_create_user(
      user_type='CUSTOMER',
      access_token='valid_google_token',
      provider='google',
      session_token=None,
      id_token=None
    )
    
    assert user.id == existing_user.id
    assert user.google_user_id == '123456789'
    assert user.auth_provider == 'google'
    assert 'Googleアカウントを追加しました' in message
  
  def test_4_3_2_add_google_to_line_user(self, mock_google_api):
    """4.3.2: 既存メール（LINE登録）にGoogleアカウント追加"""
    existing_user = UserFactory(
      email='test@example.com',
      auth_provider='line',
      line_user_id='U1234567890abcdef',
      google_user_id=None
    )
    
    user, _, message = SocialLoginService.get_or_create_user(
      user_type='CUSTOMER',
      access_token='valid_google_token',
      provider='google',
      session_token=None,
      id_token=None
    )
    
    assert user.id == existing_user.id
    assert user.google_user_id == '123456789'
    assert user.line_user_id == 'U1234567890abcdef'  # そのまま
    assert user.auth_provider == 'google'
  
  def test_4_3_3_add_google_with_picture_to_user_without_picture(self, mock_google_api):
    """4.3.3: プロフィール画像なしユーザーに追加"""
    existing_user = UserFactory(
      email='test@example.com',
      profile_image_url=None
    )
    
    user, _, _ = SocialLoginService.get_or_create_user(
      user_type='CUSTOMER',
      access_token='valid_google_token',
      provider='google',
      session_token=None,
      id_token=None
    )
    
    assert user.profile_image_url == 'https://example.com/photo.jpg'
  
  def test_4_3_4_add_google_to_user_with_picture(self, mock_google_api):
    """4.3.4: プロフィール画像ありユーザー"""
    existing_user = UserFactory(
      email='test@example.com',
      profile_image_url='https://existing.com/photo.jpg'
    )
    
    user, _, _ = SocialLoginService.get_or_create_user(
      user_type='CUSTOMER',
      access_token='valid_google_token',
      provider='google',
      session_token=None,
      id_token=None
    )
    
    # 既存の画像は更新されない
    assert user.profile_image_url == 'https://existing.com/photo.jpg'
  
  def test_4_3_5_add_google_to_unverified_email_user(self, mock_google_api):
    """4.3.5: 既存メール（is_email_verified=False）にGoogle追加"""
    existing_user = UserFactory(
      email='test@example.com',
      is_email_verified=False,
      auth_provider='email'
    )
    
    user, _, _ = SocialLoginService.get_or_create_user(
      user_type='CUSTOMER',
      access_token='valid_google_token',
      provider='google',
      session_token=None,
      id_token=None
    )
    
    assert user.google_user_id == '123456789'
    # is_email_verified は変更されない（Falseのまま）
    assert user.is_email_verified is False


@pytest.mark.django_db
class TestGoogleOwnerLogin:
  """OWNER Googleログインのテスト"""
  
  def test_4_4_1_owner_google_first_signup(self, mock_google_api):
    """4.4.1: OWNER Google初回サインアップ"""
    user, refresh, message = SocialLoginService.get_or_create_user(
      user_type='OWNER',
      access_token='valid_google_token',
      provider='google',
      session_token=None,
      id_token=None
    )
    
    assert user.user_type == 'OWNER'
    assert user.google_user_id == '123456789'
    assert user.email == 'test@example.com'
  
  def test_4_4_2_owner_google_re_login(self, mock_google_api):
    """4.4.2: OWNER Google再ログイン"""
    existing_owner = UserFactory(
      user_type='OWNER',
      email='test@example.com',
      google_user_id='123456789',
      auth_provider='google'
    )
    
    user, refresh, message = SocialLoginService.get_or_create_user(
      user_type='OWNER',
      access_token='valid_google_token',
      provider='google',
      session_token=None,
      id_token=None
    )
    
    assert user.id == existing_owner.id
    assert refresh is not None
  
  def test_4_4_3_add_google_to_existing_owner(self, mock_google_api):
    """4.4.3: 既存OWNER（email登録）にGoogle追加"""
    existing_owner = UserFactory(
      user_type='OWNER',
      email='test@example.com',
      auth_provider='email',
      google_user_id=None
    )
    
    user, _, message = SocialLoginService.get_or_create_user(
      user_type='OWNER',
      access_token='valid_google_token',
      provider='google',
      session_token=None,
      id_token=None
    )
    
    assert user.id == existing_owner.id
    assert user.google_user_id == '123456789'
    assert 'Googleアカウントを追加しました' in message


@pytest.mark.django_db
class TestGoogleStaffWithoutInvitation:
  """STAFF Googleログイン（招待なし）のテスト"""
  
  def test_4_5_1_add_google_to_active_staff(self, mock_google_api):
    """4.5.1: 既存STAFF（is_active=True）のGoogle追加"""
    existing_staff = UserFactory(
      user_type='STAFF',
      email='test@example.com',
      is_active=True,
      auth_provider='email',
      google_user_id=None
    )
    
    user, refresh, message = SocialLoginService.get_or_create_user(
      user_type='STAFF',
      access_token='valid_google_token',
      provider='google',
      session_token=None,
      id_token=None
    )
    
    assert user.id == existing_staff.id
    assert user.google_user_id == '123456789'
    assert user.auth_provider == 'google'
    assert 'Googleアカウントを追加しました' in message
  
  def test_4_5_2_google_first_login_for_existing_staff(self, mock_google_api):
    """4.5.2: 既存STAFF（email登録）のGoogle初回ログイン"""
    existing_staff = UserFactory(
      user_type='STAFF',
      email='test@example.com',
      is_active=True,
      auth_provider='email',
      google_user_id=None
    )
    
    user, _, _ = SocialLoginService.get_or_create_user(
      user_type='STAFF',
      access_token='valid_google_token',
      provider='google',
      session_token=None,
      id_token=None
    )
    
    assert user.id == existing_staff.id
    assert user.google_user_id == '123456789'
  
  def test_4_5_3_new_staff_google_signup_without_invitation(self, mock_google_api):
    """4.5.3: 新規STAFFのGoogle登録（招待なし）"""

    with pytest.raises(ValidationError):
      user, refresh, message = SocialLoginService.get_or_create_user(
        user_type='STAFF',
        access_token='valid_google_token',
        provider='google',
        session_token=None,
        id_token=None
      )



@pytest.mark.django_db
class TestGoogleStaffWithInvitation:
  """STAFF Google招待アクティベーションのテスト"""
  
  def test_4_6_1_google_invitation_activation(self, mock_google_api, query_counter):
    """4.6.1: Google招待アクティベート"""
    invitation = StaffInvitationFactory(email='test@example.com')

    session_token = 'test_session_token'
    
    cache_key = f'invitation_session:{session_token}'
    cache.set(cache_key, {
      'invitation_id': str(invitation.id),
      'invitation_token': invitation.token,
      'email': invitation.email,
    }, timeout=900)


    with query_counter as qc:
      user, refresh, message = SocialLoginService.get_or_create_user(
        user_type='STAFF',
        access_token='valid_google_token',
        provider='google',
        session_token=session_token,
        id_token=None
      )
    qc.assert_max_queries(8)

    assert hasattr(user, 'staff_progress')
    assert user.staff_progress.step == 'profile'
    
    from core.serializers import UserSerializer

    from django.test.utils import CaptureQueriesContext
    from django.db import connection
    
    user_serializer = UserSerializer(user)
    serialized_data = user_serializer.data
    
    
    assert serialized_data['progress']['step'] == 'profile'
    assert user.is_active is True
    assert user.google_user_id == '123456789'
    assert user.is_email_verified is True
    assert user.auth_provider == 'google'
    assert refresh is not None
  
  def test_4_6_2_activation_invitation_state(self, mock_google_api):
    """4.6.2: アクティベート後の招待状態"""
    invitation = StaffInvitationFactory(email='test@example.com')
    session_token = 'test_session_token'
    
    cache_key = f'invitation_session:{session_token}'
    cache.set(cache_key, {
      'invitation_id': str(invitation.id),
      'invitation_token': invitation.token,
      'email': invitation.email,
    }, timeout=900)
    
    user, _, _ = SocialLoginService.get_or_create_user(
      user_type='STAFF',
      access_token='valid_google_token',
      provider='google',
      session_token=session_token,
      id_token=None
    )
    
    invitation.refresh_from_db()
    assert invitation.is_used is True
    assert invitation.used_at is not None
  
  def test_4_6_3_activation_progress_update(self, mock_google_api):
    """4.6.3: アクティベート後のプログレス"""
    invitation = StaffInvitationFactory(email='test@example.com')
    session_token = 'test_session_token'
    
    cache_key = f'invitation_session:{session_token}'
    cache.set(cache_key, {
      'invitation_id': str(invitation.id),
      'invitation_token': invitation.token,
      'email': invitation.email,
    }, timeout=900)
    
    user, _, _ = SocialLoginService.get_or_create_user(
      user_type='STAFF',
      access_token='valid_google_token',
      provider='google',
      session_token=session_token,
      id_token=None
    )
    
    progress = user.staff_progress
    assert progress.step == 'profile'
  
  def test_4_6_4_activation_redis_cleanup(self, mock_google_api):
    """4.6.4: アクティベート後のRedis"""
    invitation = StaffInvitationFactory(email='test@example.com')
    session_token = 'test_session_token'
    
    cache_key = f'invitation_session:{session_token}'
    cache.set(cache_key, {
      'invitation_id': str(invitation.id),
      'invitation_token': invitation.token,
      'email': invitation.email,
    }, timeout=900)
    
    SocialLoginService.get_or_create_user(
      user_type='STAFF',
      access_token='valid_google_token',
      provider='google',
      session_token=session_token,
      id_token=None
    )
    
    # Redisから削除されている
    session_data = cache.get(cache_key)
    assert session_data is None
  
  def test_4_6_6_google_profile_picture_set(self, mock_google_api):
    """4.6.6: Googleプロフィール画像設定"""
    invitation = StaffInvitationFactory(email='test@example.com')
    session_token = 'test_session_token'
    
    cache_key = f'invitation_session:{session_token}'
    cache.set(cache_key, {
      'invitation_id': str(invitation.id),
      'invitation_token': invitation.token,
      'email': invitation.email,
    }, timeout=900)
    
    user, _, _ = SocialLoginService.get_or_create_user(
      user_type='STAFF',
      access_token='valid_google_token',
      provider='google',
      session_token=session_token,
      id_token=None
    )
    
    assert user.profile_image_url == 'https://example.com/photo.jpg'
  
  def test_4_6_7_invalid_session_token_google(self, mock_google_api):
    """4.6.7: 無効なsession_token（Google）"""
    with pytest.raises(ValidationError, match='セッションが無効または期限切れです'):
      SocialLoginService.get_or_create_user(
        user_type='STAFF',
        access_token='valid_google_token',
        provider='google',
        session_token='invalid_session',
        id_token=None
      )
  
  def test_4_6_8_expired_session_token_google(self, mock_google_api):
    """4.6.8: 期限切れsession_token（Google）"""
    invitation = StaffInvitationFactory(email='test@example.com')
    session_token = 'test_session_token'
    
    # Redisに保存しない（期限切れ想定）
    
    with pytest.raises(ValidationError, match='セッションが無効または期限切れです'):
      SocialLoginService.get_or_create_user(
        user_type='STAFF',
        access_token='valid_google_token',
        provider='google',
        session_token=session_token,
        id_token=None
      )
  
  def test_4_6_9_used_invitation_google(self, mock_google_api):
    """4.6.9: 使用済み招待（Google）"""
    invitation = StaffInvitationFactory(
      email='test@example.com',
      is_used=True,
      used_at=timezone.now()
    )
    session_token = 'test_session_token'
    
    cache_key = f'invitation_session:{session_token}'
    cache.set(cache_key, {
      'invitation_id': str(invitation.id),
      'invitation_token': invitation.token,
      'email': invitation.email,
    }, timeout=900)
    
    with pytest.raises(ValidationError, match='招待が見つかりません'):
      SocialLoginService.get_or_create_user(
        user_type='STAFF',
        access_token='valid_google_token',
        provider='google',
        session_token=session_token,
        id_token=None
      )
  
  def test_4_6_10_expired_invitation_google(self, mock_google_api):
    """4.6.10: 期限切れ招待（Google）"""
    invitation = StaffInvitationFactory(
      email='test@example.com',
      expires_at=timezone.now() - timedelta(days=1)
    )
    session_token = 'test_session_token'
    
    cache_key = f'invitation_session:{session_token}'
    cache.set(cache_key, {
      'invitation_id': str(invitation.id),
      'invitation_token': invitation.token,
      'email': invitation.email,
    }, timeout=900)
    
    with pytest.raises(ValidationError, match='招待が見つかりません'):
      SocialLoginService.get_or_create_user(
        user_type='STAFF',
        access_token='valid_google_token',
        provider='google',
        session_token=session_token,
        id_token=None
      )
  
  def test_4_6_11_invalid_google_token_with_invitation(self, mock_google_api_error_401):
    """4.6.11: 無効なGoogleトークン（招待あり）"""
    invitation = StaffInvitationFactory(email='test@example.com')
    session_token = 'test_session_token'
    
    cache_key = f'invitation_session:{session_token}'
    cache.set(cache_key, {
      'invitation_id': str(invitation.id),
      'invitation_token': invitation.token,
      'email': invitation.email,
    }, timeout=900)
    
    with pytest.raises(ValidationError, match='Googleトークンが無効です'):
      SocialLoginService.get_or_create_user(
        user_type='STAFF',
        access_token='invalid_token',
        provider='google',
        session_token=session_token,
        id_token=None
      )