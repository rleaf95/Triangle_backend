from django.test import TestCase, override_settings
from django.core.cache import cache
from authentication.utils.auth_rate_limiter import AuthRateLimiter


@override_settings(
  CACHES={
    'default': {
      'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
      'LOCATION': 'test-cache',
    }
  }
)
class AuthRateLimiterTestCase(TestCase):
  """認証用レート制限のテスト"""
  
  def setUp(self):
    """各テスト前にキャッシュをクリア"""
    cache.clear()
    self.auth_rate_limiter = AuthRateLimiter()
  
  def tearDown(self):
    """各テスト後にキャッシュをクリア"""
    cache.clear()
  
  def test_register_limit(self):
    """登録のレート制限 - 5回まで成功、6回目は失敗"""
    ip = '192.168.1.1'
    
    # 5回は成功
    for i in range(5):
      result = self.auth_rate_limiter.check_register_limit(ip)
      self.assertTrue(result, f"{i+1}回目の登録リクエストが拒否されました")
    
    # 6回目は失敗
    result = self.auth_rate_limiter.check_register_limit(ip)
    self.assertFalse(result, "6回目の登録リクエストが許可されました")
  
  def test_login_limit(self):
    """ログインのレート制限 - 5回まで成功、6回目は失敗"""
    ip = '192.168.1.2'
    
    # 5回は成功
    for i in range(5):
      result = self.auth_rate_limiter.check_login_limit(ip)
      self.assertTrue(result, f"{i+1}回目のログインリクエストが拒否されました")
    
    # 6回目は失敗
    result = self.auth_rate_limiter.check_login_limit(ip)
    self.assertFalse(result, "6回目のログインリクエストが許可されました")
  
  def test_email_resend_limit(self):
    """メール再送信のレート制限 - 5回まで成功、6回目は失敗"""
    ip = '192.168.1.3'
    
    # 5回は成功
    for i in range(5):
      result = self.auth_rate_limiter.check_email_resend_limit(ip)
      self.assertTrue(result, f"{i+1}回目のメール再送信リクエストが拒否されました")
    
    # 6回目は失敗
    result = self.auth_rate_limiter.check_email_resend_limit(ip)
    self.assertFalse(result, "6回目のメール再送信リクエストが許可されました")
  
  def test_different_limits_independent(self):
    """登録とログインの制限は独立している"""
    ip = '192.168.1.4'
    
    # 登録を5回実行
    for i in range(5):
      result = self.auth_rate_limiter.check_register_limit(ip)
      self.assertTrue(result)
    
    # 登録は制限される
    result = self.auth_rate_limiter.check_register_limit(ip)
    self.assertFalse(result)
    
    # ログインは影響を受けない（異なるキー）
    result = self.auth_rate_limiter.check_login_limit(ip)
    self.assertTrue(result, "ログインが登録の制限の影響を受けました")
  
  def test_get_register_reset_time(self):
    """登録制限のリセット時間取得"""
    ip = '192.168.1.5'
    
    # 1回リクエスト
    self.auth_rate_limiter.check_register_limit(ip)
    
    # リセット時間を取得
    reset_time = self.auth_rate_limiter.get_register_reset_time(ip)
    
    # LocMemCacheではTTLが取得できないため0になる
    # 実際のRedis環境では0以上の値が返る
    self.assertIsInstance(reset_time, int)
    self.assertGreaterEqual(reset_time, 0)
  
  def test_get_remaining_attempts(self):
    """残り試行回数の取得"""
    ip = '192.168.1.6'
    
    # 初期状態: 5回残っている
    remaining = self.auth_rate_limiter.get_register_remaining(ip)
    self.assertEqual(remaining, 5)
    
    # 2回リクエスト
    self.auth_rate_limiter.check_register_limit(ip)
    self.auth_rate_limiter.check_register_limit(ip)
    
    # 残り3回
    remaining = self.auth_rate_limiter.get_register_remaining(ip)
    self.assertEqual(remaining, 3)
    
    # さらに3回リクエスト
    self.auth_rate_limiter.check_register_limit(ip)
    self.auth_rate_limiter.check_register_limit(ip)
    self.auth_rate_limiter.check_register_limit(ip)
    
    # 残り0回
    remaining = self.auth_rate_limiter.get_register_remaining(ip)
    self.assertEqual(remaining, 0)
