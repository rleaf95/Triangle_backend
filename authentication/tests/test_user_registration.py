import pytest
from django.core.exceptions import ValidationError
from users.models import User, StaffProfile, CustomerRegistrationProgress
from authentication.services.user_registration_service import UserRegistrationService
from .factory import UserFactory



@pytest.mark.django_db
class TestCustomerSignup:
  """CUSTOMERサインアップのテスト"""
  
  def test_01_01_01_customer_signup_with_required_fields_only(self):
    """1.1.1: 必須項目のみでサインアップ"""
    data = {
      'email': 'customer@example.com',
      'password': 'testpass123',
    }
    
    user, refresh, message = UserRegistrationService.register_user(
      session_token=None,
      user_type='CUSTOMER',
      data=data,
    )
    
    assert user.email == 'customer@example.com'
    assert user.user_type == 'CUSTOMER'
    assert user.is_active is False
    assert user.is_email_verified is False
    assert user.auth_provider == 'email'
    assert user.check_password('testpass123')
    assert refresh is None
    assert 'メール認証リンク' in message

  def test_01_01_02_customer_signup_with_all_fields(self, query_counter):
    """1.1.2: 全項目入力でサインアップ （クエリ数検証付き）"""
    data = {
      'email': 'customer@example.com',
      'password': 'testpass123',
      'first_name': '太郎',
      'last_name': '山田',
      'phone_number': '090-1234-5678',
      'country': 'JP',
      'timezone': 'Asia/Tokyo',
      'language': 'ja',
    }
    with query_counter as qc:
      user, refresh, message = UserRegistrationService.register_user(
        session_token=None,
        user_type='CUSTOMER',
        data=data,
      )

    assert hasattr(user, '_cached_customer_progress')
    assert user._cached_customer_progress.step == 'done'
    
    from users.serializers import UserSerializer
    with query_counter as qc2:
      user_serializer = UserSerializer(user)
      serialized_data = user_serializer.data
    
    qc2.assert_max_queries(0, "Serialization時はクエリ発行なし")
    
    assert serialized_data['progress']['step'] == 'done'
    assert user.email == 'customer@example.com'
    assert user.first_name == '太郎'
    assert user.last_name == '山田'
    assert user.phone_number == '090-1234-5678'
    assert user.country == 'JP'
    assert user.timezone == 'Asia/Tokyo'
    assert user.language == 'ja'

    assert not hasattr(user, 'staff_profile')
    qc.assert_max_queries(4)
  
  
  def test_01_01_04_customer_signup_default_values(self):
    """1.1.4: デフォルト値の確認"""
    data = {
      'email': 'customer@example.com',
      'password': 'testpass123',
    }
    
    user, _, _ = UserRegistrationService.register_user(
      session_token=None,
      user_type='CUSTOMER',
      data=data,
    )
    
    assert user.country == ''
    assert user.timezone == ''
    assert user.auth_provider == 'email'
  
  
  def test_01_01_09_customer_signup_with_existing_email_active(self):
    """1.1.9: 既存のメールアドレス（is_active=True）"""
    UserFactory(email='existing@example.com', is_active=True)
    
    data = {
      'email': 'existing@example.com',
      'password': 'testpass123',
    }
    
    # IntegrityError or ValidationError が発生する想定
    with pytest.raises(ValidationError):
      UserRegistrationService.register_user(
        session_token=None,
        user_type='CUSTOMER',
        data=data,
      )
  
  def test_01_01_10_customer_signup_with_existing_email_inactive(self):
    """1.1.10: 既存のメールアドレス(is_active=False)"""
    UserFactory(email='existing@example.com', is_active=False)
    
    data = {
      'email': 'existing@example.com',
      'password': 'testpass123',
      'user_type':'CUSTOMER'
    }
    
    with pytest.raises(ValidationError, match='ログインしてください'):
      UserRegistrationService.register_user(
        session_token=None,
        user_type='CUSTOMER',
        data=data,
      )



@pytest.mark.django_db
class TestOwnerSignup:
  """OWNERサインアップのテスト"""
  
  def test_01_02_01_owner_signup_with_required_fields(self):
    """1.2.1: OWNER登録（必須項目のみ）"""
    data = {
      'email': 'owner@example.com',
      'password': 'testpass123',
    }
    
    user, _, _ = UserRegistrationService.register_user(
      session_token=None,
      user_type='OWNER',
      data=data,
    )
    
    assert user.email == 'owner@example.com'
    assert user.user_type == 'OWNER'
    assert user.is_email_verified is False
  
  def test_01_02_02_owner_signup_with_all_fields(self):
    """1.2.2: OWNER登録（全項目）"""
    data = {
      'email': 'owner@example.com',
      'password': 'testpass123',
      'first_name': '太郎',
      'last_name': '山田',
      'phone_number': '090-1234-5678',
      'country': 'JP',
      'timezone': 'Asia/Tokyo',
      'language': 'ja',
    }
    
    user, _, _ = UserRegistrationService.register_user(
      session_token=None,
      user_type='OWNER',
      data=data,
    )
    
    assert user.user_type == 'OWNER'
    assert user.first_name == '太郎'
    assert user.last_name == '山田'
  
  def test_01_02_04_owner_signup_with_existing_email(self):
    """1.2.4: 既存のメールアドレス"""
    UserFactory(email='existing@example.com', user_type='OWNER')
    
    data = {
      'email': 'existing@example.com',
      'password': 'testpass123',
    }
    
    with pytest.raises(Exception):
      UserRegistrationService.register_user(
        session_token=None,
        user_type='OWNER',
        data=data,
      )