import pytest
from authentication.serializers import SignupSerializer


@pytest.mark.django_db
class TestSignupSerializer:
  """SignupSerializer のバリデーションテスト"""
  
  def test_password_required(self):
    """パスワードが必須であることを確認"""
    data = {
      'email': 'customer@example.com',
      'user_type': 'CUSTOMER',
      # password なし
    }
    
    serializer = SignupSerializer(data=data)
    assert not serializer.is_valid()
    assert 'password' in serializer.errors
  
  def test_password_min_length(self):
    """パスワードが8文字以上であることを確認"""
    data = {
      'email': 'customer@example.com',
      'user_type': 'CUSTOMER',
      'password': '1234567',  # 7文字
    }
    
    serializer = SignupSerializer(data=data)
    assert not serializer.is_valid()
    assert 'password' in serializer.errors
  
  def test_email_required(self):
    """メールアドレスが必須であることを確認"""
    data = {
      'password': 'testpass123',
      'user_type': 'CUSTOMER',
    }
    
    serializer = SignupSerializer(data=data)
    assert not serializer.is_valid()
    assert 'email' in serializer.errors
  
  def test_invalid_email_format(self):
    """無効なメールアドレス形式を拒否"""
    data = {
      'email': 'invalid-email',
      'password': 'testpass123',
      'user_type': 'CUSTOMER',
    }
    
    serializer = SignupSerializer(data=data)
    assert not serializer.is_valid()
    assert 'email' in serializer.errors
  
  def test_valid_data(self):
    """有効なデータで検証が通ることを確認"""
    data = {
      'email': 'customer@example.com',
      'password': 'testpass123',
      'user_type': 'CUSTOMER',
    }
    
    serializer = SignupSerializer(data=data)
    assert serializer.is_valid()