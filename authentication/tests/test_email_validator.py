import pytest
from authentication.utils import DisposableEmailChecker
from unittest.mock import patch, MagicMock
import requests

class TestDisposableEmailChecker:
  """使い捨てメールチェッカーのテスト"""
  
  def test_disposable_email_from_local_list(self):
    """ローカルリストの使い捨てメールを検出"""
    assert DisposableEmailChecker.is_disposable('test@besttempmail.com') is True
    assert DisposableEmailChecker.is_disposable('test@10minutemailbox.com') is True
    assert DisposableEmailChecker.is_disposable('test@guerrillamail.com') is True
  
  def test_normal_email_allowed(self):
    """通常のメールアドレスは許可"""
    assert DisposableEmailChecker.is_disposable('test@gmail.com') is False
    assert DisposableEmailChecker.is_disposable('test@yahoo.com') is False
    assert DisposableEmailChecker.is_disposable('test@company.com') is False
  
  def test_case_insensitive(self):
    """大文字小文字を区別しない"""
    assert DisposableEmailChecker.is_disposable('test@BestTempMail.COM') is True
    assert DisposableEmailChecker.is_disposable('TEST@besttempmail.com') is True
  
  def test_invalid_email_format(self):
    """不正な形式のメールアドレス"""
    assert DisposableEmailChecker.is_disposable('invalid-email') is False
    assert DisposableEmailChecker.is_disposable('') is False
    assert DisposableEmailChecker.is_disposable(None) is False
  
  @patch('authentication.utils.email_validator.requests.get')
  def test_api_check_disposable(self, mock_get):
    """APIで使い捨てメールを検出"""
    # APIレスポンスをモック
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'disposable': True}
    mock_get.return_value = mock_response
    
    # ローカルリストにないドメイン
    with patch('django.conf.settings.USE_DISPOSABLE_EMAIL_API', True):
      result = DisposableEmailChecker._check_with_api('newdisposable.com')
      assert result is True
  
  @patch('authentication.utils.email_validator.requests.get')
  def test_api_check_normal(self, mock_get):
    """APIで通常メールを判定"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'disposable': False}
    mock_get.return_value = mock_response
    
    with patch('django.conf.settings.USE_DISPOSABLE_EMAIL_API', True):
      result = DisposableEmailChecker._check_with_api('legitimate.com')
      assert result is False
  
  @patch('authentication.utils.email_validator.requests.get')
  def test_api_timeout_returns_false(self, mock_get):
    """APIタイムアウト時はFalseを返す"""
    mock_get.side_effect = requests.Timeout()
    
    result = DisposableEmailChecker._check_with_api('test.com')
    assert result is False
  
  @patch('authentication.utils.email_validator.requests.get')
  def test_api_error_returns_false(self, mock_get):
    """APIエラー時はFalseを返す"""
    mock_get.side_effect = Exception('API Error')
    
    result = DisposableEmailChecker._check_with_api('test.com')
    assert result is False


class TestDisposableEmailInSerializer:
  """Serializerでの使い捨てメールチェック"""
  
  def test_register_with_disposable_email(self):
    """使い捨てメールで登録を試みる"""
    from authentication.serializers import OwnerSignupSerializer
    
    data = {
      'email': 'test@besttempmail.com',
      'password': 'SecurePass123!',
      'user_type': 'OWNER'
    }
    
    serializer = OwnerSignupSerializer(data=data)
    assert serializer.is_valid() is False
    assert 'email' in serializer.errors
    assert '使い捨て' in str(serializer.errors['email'])
  
  def test_register_with_normal_email(self):
    """通常のメールで登録"""
    from authentication.serializers import OwnerSignupSerializer
    
    data = {
      'email': 'test@gmail.com',
      'password': 'SecurePass123!',
      'user_type': 'OWNER'
    }
    
    serializer = OwnerSignupSerializer(data=data)
    assert serializer.is_valid() is True