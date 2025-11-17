from django.urls import path
from .views import login, registration

urlpatterns = [
  path('business_register/', registration.OwnerRegisterView.as_view(), name='business-register' ),
  path('register/', registration.CustomerRegisterView.as_view(), name='customer-register'),

  path('email/verify/', registration.VerifyEmailView.as_view(), name='email_verify'),
  path('email/verify/resend/', registration.ResendVerificationEmailView, name='verify-email-resend'),
  path('email/verify/change/', registration.ChangePendingEmailView, name='verify-email-change'),

  path('customer/login/', login.CustomerLoginView.as_view(), name='customer-login'),
  path('customer/register/', login.CustomerRegisterView.as_view(), name='customer-register'),
  
  path('staff/login/', login.StaffOwnerLoginView.as_view(), name='staff-owner-login'),
  path('staff/register/', login.StaffOwnerRegisterView.as_view(), name='staff-owner-register'),
]