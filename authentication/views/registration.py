import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from authentication.utils import AuthRateLimiter
from rest_framework.exceptions import Throttled

from ..serializers import OwnerSignupSerializer, CustomerSignupSerializer,  EmailChangeSerializer
from users.serializers import UserSerializer
from ..services import UserRegistrationService
from rest_framework.exceptions import ValidationError, NotFound
from common.service import EmailSendException
from django.utils.translation import gettext as _
from .mixins import TokenResponseMixin
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from common.utils.request_utils import get_client_ip


class OwnerRegisterView(APIView):
	permission_classes = [AllowAny]

	def post(self, request):
		rate_limiter = AuthRateLimiter()
		ip = get_client_ip(request)
			
		if not rate_limiter.check_register_limit(ip):
			remaining_time = rate_limiter.get_register_reset_time(
				f"auth:register:{ip}"
			)
			raise Throttled(
				detail=_('Too many attempts.Please try again in %(remaining_time)s seconds.') % {
					'remaining_time': remaining_time
				}
			)
		
		serializer = OwnerSignupSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		try:
			is_link_social, message = UserRegistrationService.register_pending_user(
				email=serializer.validated_data['email'],
				password=serializer.validated_data['password'],
				user_type='OWNER',
				country=serializer.validated_data['country'],				
				user_timezone=serializer.validated_data['user_timezone'],
				last_name=serializer.validated_data['last_name'],
				first_name=serializer.validated_data['first_name'],
			)
		except (ValidationError, EmailSendException):
			raise

		return Response({
		'is_link_social': is_link_social,
		'detail': message,
	}, status=status.HTTP_201_CREATED)


class CustomerRegisterView(APIView):
	permission_classes = [AllowAny]
	
	def post(self, request):
		serializer = CustomerSignupSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		
		try:
			is_link_social, message = UserRegistrationService.register_pending_user(
				email=serializer.validated_data['email'],
				password=serializer.validated_data['password'],
				user_type='OWNER',
				country=serializer.validated_data['country'],				
				user_timezone=serializer.validated_data['user_timezone'],
				last_name=serializer.validated_data['last_name'],
				first_name=serializer.validated_data['first_name'],		
			)
		except (ValidationError, EmailSendException):
			raise
		
		return Response({
		'is_link_social': is_link_social,
		'detail': message,
	}, status=status.HTTP_201_CREATED)


class VerifyEmailView(TokenResponseMixin, APIView):
	permission_classes = [AllowAny]

	@method_decorator(ensure_csrf_cookie)
	def post(self, request):
		token = request.data.get('token')
		platform = self.get_platform(request)

		try:
			user, is_link_social, message  = UserRegistrationService.verify_and_activate(token)
		except (NotFound, ValidationError):
			raise

		refresh = RefreshToken.for_user(user)
		access_token = str(refresh.access_token)
		refresh_token = str(refresh)
		
		serializer = UserSerializer(user, fields=['id', 'email', 'first_name', 'last_name', 'user_type', 'progress'])
		response_data = {
      'detail': message,
      'user': serializer.data,
      'is_link_social': is_link_social
    }

		return self.create_token_response(access_token, refresh_token, response_data, status.HTTP_201_CREATED, platform)


class ResendVerificationEmailView(APIView):
	permission_classes = [AllowAny]

	"""確認メール再送信"""
	def post(self, request):
		rate_limiter = AuthRateLimiter()
		ip = get_client_ip(request)
			
		if not rate_limiter.check_email_resend_limit(ip):
			remaining_time = rate_limiter.get_email_resend_reset_time(
				f"auth:register:{ip}"
			)
			raise Throttled(
				detail=_('Too many attempts.Please try again in %(remaining_time)s seconds.') % {
					'remaining_time': remaining_time
				}
			)
		
		email = request.data.get('email')
		try:
			UserRegistrationService.resend_verification_email(email)
		except (NotFound, EmailSendException):
			raise
		
		return Response(
			{'detail': _('The verification email has been resent.')},
			status=status.HTTP_200_OK
    )

class ChangePendingEmailView(APIView):
	permission_classes = [AllowAny]

	"""仮登録中のメールアドレス変更"""
	def post(self, request):
		rate_limiter = AuthRateLimiter()
		ip = get_client_ip(request)
			
		if not rate_limiter.check_email_resend_limit(ip):
			remaining_time = rate_limiter.get_email_resend_reset_time(
				f"auth:register:{ip}"
			)
			raise Throttled(
				detail=_('Too many attempts.Please try again in %(remaining_time)s seconds.') % {
					'remaining_time': remaining_time
				}
			)
		serializer = EmailChangeSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		old_email=serializer.validated_data['old_email']
		new_email=serializer.validated_data['new_email']

		try:
			pending_user = UserRegistrationService.change_pending_email(old_email, new_email)
		except (NotFound, EmailSendException):
			raise

		return Response({
			'detail': _('The verification email has been resent to %(new_email)s.')%{'new_email':new_email},
		},status=status.HTTP_200_OK)