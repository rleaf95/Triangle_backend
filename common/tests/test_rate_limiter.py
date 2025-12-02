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
    """
    レート制限をチェック
    
    Args:
      key: キャッシュキー
      limit: 制限回数
      period: 制限期間（秒）
    
    Returns:
      True: リクエスト許可, False: レート制限超過
    """
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
      # エラー時は寛容にリクエストを許可
      return True
  
  def get_remaining(self, key: str, limit: int) -> int:
    """
    残りのリクエスト可能回数を取得
    
    Args:
      key: キャッシュキー
      limit: 制限回数
    
    Returns:
      残りのリクエスト可能回数
    """
    try:
      current = cache.get(key)
      if current is None:
        return limit
      return max(0, limit - int(current))
    except Exception:
      return limit
  
  def get_reset_time(self, key: str) -> int:
    """
    レート制限がリセットされるまでの秒数を取得
    
    Note: この機能はRedis使用時のみ正確に動作します
    
    Args:
      key: キャッシュキー
    
    Returns:
      リセットまでの秒数（Redis未使用時は0）
    """
    if self.redis_client is None:
      return 0
    
    try:
      ttl = self.redis_client.ttl(key)
      return ttl if ttl > 0 else 0
    except Exception as e:
      logger.error(f"Error getting reset time: {e}")
      return 0
  
  def reset(self, key: str) -> None:
    """
    レート制限をリセット（主にテスト用）
    
    Args:
      key: キャッシュキー
    """
    try:
      cache.delete(key)
    except Exception as e:
      logger.error(f"Error resetting rate limit: {e}")