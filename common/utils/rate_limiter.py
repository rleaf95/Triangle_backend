from .redis_client import get_redis_client
from rest_framework.exceptions import Throttled
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
  """汎用レート制限（どのアプリからも使用可能）"""
  
  def __init__(self):
    self.redis_client = get_redis_client()
  
  def check_rate_limit(self, key, limit, period):
    try:
      current = self.redis_client.get(key)
      if current is None:
        self.redis_client.setex(key, period, 1)
        return True
      
      current = int(current)
      if current >= limit:
        logger.warning(f"Rate limit exceeded for key: {key}")
        return False
      
      self.redis_client.incr(key)
      return True
        
    except Exception as e:
      logger.error(f"Redis error in rate limiting: {str(e)}")
      return True
    
  def get_remaining(self, key, limit):
    """残り試行回数を取得"""
    try:
      current = self.redis_client.get(key)
      if current is None:
        return limit
      return max(0, limit - int(current))
    except Exception:
        return limit
  
  def get_reset_time(self, key):
    """リセットまでの秒数を取得"""
    try:
      ttl = self.redis_client.ttl(key)
      return ttl if ttl > 0 else 0
    except Exception:
      return 0