from common.utils import RateLimiter

class AuthRateLimiter:
  """認証エンドポイント用のレート制限"""
  
  REGISTER_LIMIT = 5
  REGISTER_PERIOD = 3600
  
  LOGIN_LIMIT = 5
  LOGIN_PERIOD = 3600
  
  EMAIL_RESEND_LIMIT = 5
  EMAIL_RESEND_PERIOD = 3600
  
  def __init__(self):
    self.rate_limiter = RateLimiter()
  
  def check_register_limit(self, identifier):
    """登録のレート制限チェック"""
    key = f"auth:register:{identifier}"
    return self.rate_limiter.check_rate_limit(
      key, 
      self.REGISTER_LIMIT, 
      self.REGISTER_PERIOD
    )
  
  def check_login_limit(self, identifier):
    """ログインのレート制限チェック"""
    key = f"auth:login:{identifier}"
    return self.rate_limiter.check_rate_limit(
      key, 
      self.LOGIN_LIMIT, 
      self.LOGIN_PERIOD
    )
  
  def check_email_resend_limit(self, identifier):
    """メール再送信のレート制限チェック"""
    key = f"auth:email_resend:{identifier}"
    return self.rate_limiter.check_rate_limit(
      key, 
      self.EMAIL_RESEND_LIMIT, 
      self.EMAIL_RESEND_PERIOD
    )
