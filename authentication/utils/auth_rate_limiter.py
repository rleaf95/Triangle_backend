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

  # ========================================
  # 登録関連
  # ========================================
  
  def check_register_limit(self, identifier):
    key = self._get_register_key(identifier)
    return self.rate_limiter.check_rate_limit(
      key, 
      self.REGISTER_LIMIT, 
      self.REGISTER_PERIOD
    )
  def get_register_remaining(self, identifier):
    key = self._get_register_key(identifier)
    return self.rate_limiter.get_remaining(key, self.REGISTER_LIMIT)
  
  def get_register_reset_time(self, identifier):
    key = self._get_register_key(identifier)
    return self.rate_limiter.get_reset_time(key)
  
  def _get_register_key(self, identifier):
    return f"auth:register:{identifier}"
  

  # ========================================
  # ログイン
  # ========================================
  def check_login_limit(self, identifier):
    key = self._get_login_key(identifier)
    return self.rate_limiter.check_rate_limit(
      key, 
      self.LOGIN_LIMIT, 
      self.LOGIN_PERIOD
    )
  
  def get_login_remaining(self, identifier):
    key = self._get_login_key(identifier)
    return self.rate_limiter.get_remaining(key, self.LOGIN_LIMIT)
  
  def get_login_reset_time(self, identifier):
    key = self._get_login_key(identifier)
    return self.rate_limiter.get_reset_time(key)
  
  def _get_login_key(self, identifier):
    return f"auth:login:{identifier}"
  
  # ========================================
  # メール再送信
  # ========================================
  def check_email_resend_limit(self, identifier):
    key = f"auth:email_resend:{identifier}"
    return self.rate_limiter.check_rate_limit(
      key, 
      self.EMAIL_RESEND_LIMIT, 
      self.EMAIL_RESEND_PERIOD
    )
  def get_email_resend_remaining(self, identifier):
    key = self._get_email_resend_key(identifier)
    return self.rate_limiter.get_remaining(key, self.EMAIL_RESEND_LIMIT)
  
  def get_email_resend_reset_time(self, identifier):
    key = self._get_email_resend_key(identifier)
    return self.rate_limiter.get_reset_time(key)

  def _get_email_resend_key(self, identifier):
    return f"auth:email_resend:{identifier}"
