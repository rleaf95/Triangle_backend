from django.test import TestCase
from unittest.mock import patch
import fakeredis
from common.utils import RateLimiter
from authentication.utils.auth_rate_limiter import AuthRateLimiter

class RateLimiterTestCase(TestCase):
  def setUp(self):
    """テスト用のfake Redisを設定"""
    self.fake_redis = fakeredis.FakeStrictRedis(decode_responses=True)
    self.rate_limiter = RateLimiter()
    self.rate_limiter.redis_client = self.fake_redis
  
  def test_first_request_allowed(self):
    """初回リクエストは許可される"""
    result = self.rate_limiter.check_rate_limit(
      key='test:user1',
      limit=5,
      period=3600
    )
    self.assertTrue(result)
  
  def test_within_limit_allowed(self):
    """制限内のリクエストは許可される"""
    key = 'test:user2'
    
    for i in range(5):
      result = self.rate_limiter.check_rate_limit(key, 5, 3600)
      self.assertTrue(result, f"{i+1}回目のリクエストが拒否されました")

  def test_exceed_limit_blocked(self):
    """制限を超えるリクエストはブロックされる"""
    key = 'test:user3'
    
    # 5回は成功
    for i in range(5):
      self.rate_limiter.check_rate_limit(key, 5, 3600)
    
    # 6回目は失敗
    result = self.rate_limiter.check_rate_limit(key, 5, 3600)
    self.assertFalse(result)
  
  def test_different_keys_independent(self):
    """異なるキーは独立してカウントされる"""
    # user1が5回リクエスト
    for i in range(5):
      self.rate_limiter.check_rate_limit('test:user1', 5, 3600)
    
    # user2の初回リクエストは成功
    result = self.rate_limiter.check_rate_limit('test:user2', 5, 3600)
    self.assertTrue(result)
  
  def test_get_remaining_attempts(self):
    """残り試行回数の取得"""
    key = 'test:user4'
    limit = 5
    
    # 初期状態
    remaining = self.rate_limiter.get_remaining(key, limit)
    self.assertEqual(remaining, 5)
    
    # 2回リクエスト
    self.rate_limiter.check_rate_limit(key, limit, 3600)
    self.rate_limiter.check_rate_limit(key, limit, 3600)
    
    # 残り3回
    remaining = self.rate_limiter.get_remaining(key, limit)
    self.assertEqual(remaining, 3)
  
  def test_expiry_resets_counter(self):
    """有効期限が切れるとカウンターがリセットされる"""
    key = 'test:user5'
    
    # 5回リクエスト（上限に達する）
    for i in range(5):
      self.rate_limiter.check_rate_limit(key, 5, 1)  # 1秒で期限切れ
    
    # 上限に達している
    result = self.rate_limiter.check_rate_limit(key, 5, 1)
    self.assertFalse(result)
    
    # キーを削除（期限切れをシミュレート）
    self.fake_redis.delete(key)
    
    # 再度リクエスト可能
    result = self.rate_limiter.check_rate_limit(key, 5, 1)
    self.assertTrue(result)


class AuthRateLimiterTestCase(TestCase):
  """認証用レート制限のテスト"""
  
  def setUp(self):
    self.fake_redis = fakeredis.FakeStrictRedis(decode_responses=True)
    self.auth_rate_limiter = AuthRateLimiter()
    self.auth_rate_limiter.rate_limiter.redis_client = self.fake_redis
  
  def test_register_limit(self):
    """登録のレート制限"""
    ip = '192.168.1.1'
    
    # 5回は成功
    for i in range(5):
      result = self.auth_rate_limiter.check_register_limit(ip)
      self.assertTrue(result)
    
    # 6回目は失敗
    result = self.auth_rate_limiter.check_register_limit(ip)
    self.assertFalse(result)
  
  def test_login_limit(self):
    """ログインのレート制限"""
    ip = '192.168.1.2'
    
    for i in range(5):
      result = self.auth_rate_limiter.check_login_limit(ip)
      self.assertTrue(result)
    
    # 11回目は失敗
    result = self.auth_rate_limiter.check_login_limit(ip)
    self.assertFalse(result)
  
  def test_different_limits_independent(self):
    """登録とログインの制限は独立している"""
    ip = '192.168.1.3'
    
    for i in range(5):
      self.auth_rate_limiter.check_register_limit(ip)
    
    result = self.auth_rate_limiter.check_login_limit(ip)
    self.assertTrue(result)
