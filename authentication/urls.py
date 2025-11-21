from django.urls import path
from authentication.views import (
  CurrentUserView,
  CustomerLoginView,
  StaffOwnerLoginView,
  RefreshTokenView,
  OwnerRegisterView, 
  CustomerRegisterView, 
  VerifyEmailView,
  ResendVerificationEmailView,
  ChangePendingEmailView
)

urlpatterns = [
  path('me/', CurrentUserView.as_view(), name='current-user'),
  path('refresh/', RefreshTokenView.as_view(), name='current-user'),
  path('login/', CustomerLoginView.as_view(), name='customer-login'),
  path('business_login/', StaffOwnerLoginView.as_view(), name='business-login'),
  path('register/', CustomerRegisterView.as_view(), name='customer-register'),
  path('business_register/', OwnerRegisterView.as_view(), name='business-register'),
  path('email/verify/', VerifyEmailView.as_view(), name='email-verify'),
  path('email/verify/resend/', ResendVerificationEmailView.as_view(), name='email-verify-resend'),
  path('email/verify/change/', ChangePendingEmailView.as_view(), name='email-verify-change')
]