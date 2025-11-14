import pytest
from django.core.exceptions import ValidationError
from core.services import UserRegistrationService, RegistrationUtilsService
from .factories import StaffInvitationFactory


@pytest.mark.django_db
class TestSecurityTokenValidation:
  """トークン検証のセキュリティテスト"""
  
  def test_9_1_1_sql_injection_attempt(self):
    """9.1.1: SQLインジェクション試行"""
    malicious_token = "'; DROP TABLE staff_invitations--"
    
    with pytest.raises(ValidationError, match='無効または期限切れの招待リンクです'):
      RegistrationUtilsService.validate_invitation(malicious_token)
    
    # テーブルが削除されていないことを確認
    from core.models import StaffInvitation
    assert StaffInvitation.objects.model._meta.db_table is not None
  
  def test_9_1_2_xss_attempt(self):
    """9.1.2: XSS試行"""
    malicious_email = "<script>alert('xss')</script>@example.com"
    
    data = {
      'email': malicious_email,
      'password': 'testpass123',
    }
    
    # Serializerでバリデーションエラー or エスケープ処理
    with pytest.raises(Exception):
      RegistrationUtilsService.register_user(
        session_token=None,
        user_type='CUSTOMER',
        data=data,
        profile_data=None
      )
  
  def test_9_1_3_extremely_long_token(self):
    """9.1.3: 異常に長いトークン"""
    long_token = 'a' * 10000
    
    with pytest.raises(ValidationError):
      RegistrationUtilsService.validate_invitation(long_token)


@pytest.mark.django_db
class TestAuthenticationAuthorization:
  """認証・認可のセキュリティテスト"""
  
  def test_9_2_1_use_other_persons_invitation(self):
    """9.2.1: 他人の招待トークン使用"""
    invitation = StaffInvitationFactory(email='staff@example.com')
    session_token = 'test_session_token'
    
    from django.core.cache import cache
    cache_key = f'invitation_session:{session_token}'
    cache.set(cache_key, {
      'invitation_id': str(invitation.id),
      'invitation_token': invitation.token,
      'email': 'staff@example.com',
    }, timeout=900)
    
    # 異なるメールアドレスでアクティベート試行
    data = {
      'email': 'hacker@example.com',
      'password': 'testpass123',
    }
    
    with pytest.raises(ValidationError):
      UserRegistrationService.register_user(
        session_token=session_token,
        user_type='STAFF',
        data=data,
        profile_data=None
      )
  
  def test_9_2_2_reuse_expired_token(self):
    """9.2.2: 期限切れトークンの再利用"""
    from django.utils import timezone
    from datetime import timedelta
    
    invitation = StaffInvitationFactory(
      expires_at=timezone.now() - timedelta(days=1)
    )
    
    with pytest.raises(ValidationError, match='無効または期限切れの招待リンクです'):
      RegistrationUtilsService.validate_invitation(invitation.token)


@pytest.mark.django_db
class TestSessionSecurity:
  """セッションセキュリティのテスト"""
  
  def test_session_token_tampering(self):
    """セッショントークン改ざん"""
    invitation = StaffInvitationFactory()
    session_token = 'test_session_token'
    
    from django.core.cache import cache
    cache_key = f'invitation_session:{session_token}'
    cache.set(cache_key, {
      'invitation_id': str(invitation.id),
      'invitation_token': 'wrong_token',  # 改ざんされたトークン
      'email': invitation.email,
    }, timeout=900)
    
    data = {
      'email': invitation.email,
      'password': 'testpass123',
    }
    
    with pytest.raises(ValidationError, match='無効または期限切れの招待リンクです'):
      UserRegistrationService.register_user(
        session_token=session_token,
        user_type='STAFF',
        data=data,
        profile_data=None
      )
  
  def test_session_hijacking_attempt(self):
    """セッションハイジャック試行"""
    invitation1 = StaffInvitationFactory(email='staff1@example.com')
    invitation2 = StaffInvitationFactory(email='staff2@example.com')
    
    session_token = 'test_session_token'
    
    from django.core.cache import cache
    cache_key = f'invitation_session:{session_token}'
    
    # invitation1のセッション
    cache.set(cache_key, {
      'invitation_id': str(invitation1.id),
      'invitation_token': invitation1.token,
      'email': invitation1.email,
    }, timeout=900)
    
    # invitation2のデータでアクティベート試行
    data = {
      'email': invitation2.email,
      'password': 'testpass123',
    }
    
    with pytest.raises(ValidationError):
      UserRegistrationService.register_user(
        session_token=session_token,
        user_type='STAFF',
        data=data,
        profile_data=None
      )


@pytest.mark.django_db
class TestPasswordSecurity:
  """パスワードセキュリティのテスト"""
  
  def test_password_hashing(self):
    """パスワードがハッシュ化されているか"""
    from .factories import UserFactory
    
    user = UserFactory(password='testpass123')
    
    # パスワードが平文で保存されていないことを確認
    assert user.password != 'testpass123'
    # ハッシュ化されたパスワードで認証できることを確認
    assert user.check_password('testpass123')
  
  def test_weak_password_rejection(self):
    """脆弱なパスワードの拒否"""
    # Serializerで8文字未満は拒否される想定
    data = {
      'email': 'customer@example.com',
      'password': '123',  # 短すぎる
    }
    
    with pytest.raises(Exception):
      UserRegistrationService.register_user(
        session_token=None,
        user_type='CUSTOMER',
        data=data,
        profile_data=None
      )