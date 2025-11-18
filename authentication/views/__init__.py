from .registration import (
  OwnerRegisterView, 
  CustomerRegisterView,
  ResendVerificationEmailView,
  ChangePendingEmailView,
  VerifyEmailView
)
from .activation import ActivateAPIView

__all__ = [
  'OwnerRegisterView',
  'CustomerRegisterView',
  'VerifyEmailView',
  'ResendVerificationEmailView',
  'ChangePendingEmailView',
  'ActivateAPIView'
]