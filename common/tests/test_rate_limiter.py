import pytest
from common.utils.rate_limiter import RateLimiter


class TestRateLimiter:
  
  def test_first_request_allowed(self):
    rate_limiter = RateLimiter()
    
    result = rate_limiter.check_rate_limit('test:user1', 5, 3600)
    assert result is True
  
  def test_within_limit_allowed(self, ):
    rate_limiter = RateLimiter()
    key = 'test:user2'
    
    for i in range(5):
      result = rate_limiter.check_rate_limit(key, 5, 3600)
      assert result is True

  def test_exceed_limit_blocked(self, ):
    """制限を超えるリクエストはブロックされる"""
    rate_limiter = RateLimiter()
    key = 'test:user3'
    
    for i in range(5):
      rate_limiter.check_rate_limit(key, 5, 3600)
    
    result = rate_limiter.check_rate_limit(key, 5, 3600)
    assert result is False
  
  def test_different_keys_independent(self, ):
    rate_limiter = RateLimiter()
    
    for i in range(5):
      rate_limiter.check_rate_limit('test:user1', 5, 3600)
    
    result = rate_limiter.check_rate_limit('test:user2', 5, 3600)
    assert result is True

  def test_get_remaining_attempts(self, ):
    """残り試行回数の取得"""
    rate_limiter = RateLimiter()
    key = 'test:user4'
    limit = 5
    
    remaining = rate_limiter.get_remaining(key, limit)
    assert remaining == 5
    
    rate_limiter.check_rate_limit(key, limit, 3600)
    rate_limiter.check_rate_limit(key, limit, 3600)
    
    remaining = rate_limiter.get_remaining(key, limit)
    assert remaining == 3
  
  def test_get_reset_time(self, ):
    """リセット時間の取得"""
    rate_limiter = RateLimiter()
    key = 'test:user5'
    
    rate_limiter.check_rate_limit(key, 5, 3600)
    
    reset_time = rate_limiter.get_reset_time(key)
    assert 0 < reset_time <= 3600
  
  def test_redis_error_handling(self, ):
    """Redisエラー時の挙動"""
    rate_limiter = RateLimiter()
    
    # Redisを壊す
    rate_limiter.redis_client.get = lambda x: (_ for _ in ()).throw(Exception('Redis error'))
    
    # エラー時はリクエストを許可（サービス継続優先）
    result = rate_limiter.check_rate_limit('test:error', 5, 3600)
    assert result is True
  
  @pytest.mark.parametrize("limit,attempts,expected", [
    (5, 3, True),
    (5, 5, True),
    (5, 6, False),
    (10, 9, True),
    (10, 11, False),
    (1, 1, True),
    (1, 2, False),
  ])
  def test_various_limits(self, limit, attempts, expected):
    """様々な制限値でのパラメータ化テスト"""
    rate_limiter = RateLimiter()
    key = f'test:param:{limit}:{attempts}'
    
    for i in range(attempts - 1):
      rate_limiter.check_rate_limit(key, limit, 3600)
    
    result = rate_limiter.check_rate_limit(key, limit, 3600)
    assert result is expected