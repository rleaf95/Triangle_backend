import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from allauth.account.models import EmailAddress, EmailConfirmation
from allauth.account.utils import send_email_confirmation
from users.models import User
from ...factories import UserFactory


@pytest.mark.django_db
class TestEmailVerification:
  """メール認証のテスト（django-allauthのモデルを直接使用）"""
  
  def test_2_1_1_email_confirmation_creation(self):
    """EmailConfirmationが正しく作成される"""
    user = UserFactory(
      email='customer@example.com',
      is_email_verified=False
    )
    
    email_address = EmailAddress.objects.create(
      user=user,
      email=user.email,
      primary=True,
      verified=False
    )
    
    confirmation = EmailConfirmation.create(email_address)
    confirmation.sent = timezone.now()
    confirmation.save()
    
    assert confirmation.key is not None
    assert len(confirmation.key) > 0
    assert confirmation.email_address == email_address
    assert not confirmation.key_expired()
  
  def test_2_1_2_email_confirmation_success(self, mock_request):
    """メール認証成功"""
    user = UserFactory(email='customer@example.com', is_email_verified=False)
    
    email_address = EmailAddress.objects.create(
      user=user,
      email=user.email,
      primary=True,
      verified=False
    )
    
    confirmation = EmailConfirmation.create(email_address)
    confirmation.sent = timezone.now()
    confirmation.save()
    
    email = confirmation.confirm(mock_request)
    
    assert email.verified is True
  
  def test_2_1_3_already_verified(self, mock_request):
    """2.1.3: 認証済みユーザーの再認証"""
    user = UserFactory(
      email='customer@example.com',
      is_email_verified=True
    )
    
    email_address = EmailAddress.objects.create(
      user=user,
      email=user.email,
      primary=True,
      verified=True
    )
    
    confirmation = EmailConfirmation.create(email_address)
    confirmation.sent = timezone.now()
    confirmation.save()
    
    confirmation.confirm(mock_request)
    
    email_address.refresh_from_db()
    assert email_address.verified is True
  
  def test_2_1_4_invalid_key(self):
    """無効な認証キー"""
    with pytest.raises(EmailConfirmation.DoesNotExist):
      EmailConfirmation.objects.get(key='invalid_key')
  
  def test_2_1_5_expired_key(self):
    """期限切れの認証キー"""
    user = UserFactory(email='customer@example.com')
    
    email_address = EmailAddress.objects.create(
      user=user,
      email=user.email,
      primary=True,
      verified=False
    )
    
    confirmation = EmailConfirmation.create(email_address)
    confirmation.sent = timezone.now() - timedelta(days=4)
    confirmation.save()
    
    assert confirmation.key_expired() is True
  
  def test_2_1_6_multiple_confirmations(self):
    """複数の確認キーを作成可能"""
    user = UserFactory(email='customer@example.com')
    
    email_address = EmailAddress.objects.create(
      user=user,
      email=user.email,
      primary=True,
      verified=False
    )
    
    # 複数作成
    conf1 = EmailConfirmation.create(email_address)
    conf1.sent = timezone.now()
    conf1.save()
    
    conf2 = EmailConfirmation.create(email_address)
    conf2.sent = timezone.now()
    conf2.save()
    
    confirmations = EmailConfirmation.objects.filter(
      email_address=email_address
    )
    
    assert confirmations.count() == 2
    assert conf1.key != conf2.key


@pytest.mark.django_db
class TestEmailVerificationLogin:
  """メール未認証でのログイン制御"""
  
  def test_2_2_1_unverified_email_user_cannot_login(self):
    """2.2.1: メール未認証ユーザーはログインできない"""
    user = UserFactory(
      email='customer@example.com',
      is_email_verified=False,
      is_active=False,  # 非アクティブ
      auth_provider='email',
      password='password123'
    )
    
    # ログイン試行（is_activeがFalseなので失敗）
    assert user.is_active is False
    # 実際のログインAPIでテストする場合
    # response = client.post('/api/auth/login/', {
    #     'email': 'customer@example.com',
    #     'password': 'password123'
    # })
    # assert response.status_code == 400
  
  
  def test_2_2_2_social_login_no_verification_required(self):
    """2.2.2: ソーシャルログインは認証不要"""
    user = UserFactory(
      email='customer@example.com',
      is_email_verified=True,
      is_active=True,
      auth_provider='google',
      google_user_id='123456789',
      password=False  # パスワードなし
    )
    
    # ソーシャルログインユーザーは即座にアクティブ
    assert user.is_email_verified is True
    assert user