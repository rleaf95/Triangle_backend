from django.core.cache import cache
from django_redis import get_redis_connection
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
  """汎用レート制限（どのアプリからも使用可能）"""
  
  def __init__(self):
    self.redis_client = None
    try:
      self.redis_client = get_redis_connection("default")
    except Exception as e:
      logger.warning(f"Redis connection not available: {e}")

  def check_rate_limit(self, key: str, limit: int, period: int) -> bool:
    try:
      current = cache.get(key)
      
      if current is None:
        cache.set(key, 1, timeout=period)
        return True
      
      current = int(current)
      if current >= limit:
        logger.warning(f"Rate limit exceeded for key: {key}")
        return False
      cache.incr(key)
      return True
      
    except Exception as e:
      logger.error(f"Cache error in rate limiting: {str(e)}")
      return True
  
  def get_remaining(self, key: str, limit: int) -> int:
    try:
      current = cache.get(key)
      if current is None:
        return limit
      return max(0, limit - int(current))
    except Exception:
        return limit
  
  def get_reset_time(self, key: str) -> int:
    """
    Note: この機能はRedis使用時のみ正確に動作します
    Returns:リセットまでの秒数-Redis未使用時は0
    """
    if self.redis_client is None:
      return 0
    
    try:
      ttl = self.redis_client.ttl(key)
      return ttl if ttl > 0 else 0
    except Exception:
      return 0