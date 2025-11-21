import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
<<<<<<< HEAD
=======
# from django.core.cache import cache
>>>>>>> main
from rest_framework_simplejwt.tokens import RefreshToken
from authentication.utils import AuthRateLimiter
from rest_framework.exceptions import Throttled

from ..serializers import OwnerSignupSerializer, CustomerSignupSerializer
from users.serializers import UserSerializer
from ..services import UserRegistrationService
from rest_framework.exceptions import ValidationError, NotFound
from common.service import EmailSendException
from django.utils.translation import gettext as _
<<<<<<< HEAD
from .mixins import TokenResponseMixin
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
=======
>>>>>>> main


class OwnerRegisterView(APIView):
	permission_classes = [AllowAny]
<<<<<<< HEAD

=======
	
>>>>>>> main
	def post(self, request):
		rate_limiter = AuthRateLimiter()
		ip = self.get_client_ip(request)
			
		if not rate_limiter.check_register_limit(ip):
			remaining_time = rate_limiter.get_register_reset_time(
				f"auth:register:{ip}"
			)
			raise Throttled(
<<<<<<< HEAD
				detail=_('試行回数が多すぎます。%(remaining_time)s秒後に再試行してください') % {
					'remaining_time': remaining_time
				}
			)
=======
    detail=_('試行回数が多すぎます。%(remaining_time)s秒後に再試行してください') % {
      'remaining_time': remaining_time
    }
  )
>>>>>>> main
		
		serializer = OwnerSignupSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		try:
			pending_user, is_link_social, message = UserRegistrationService.register_pending_user(
				email=serializer.validated_data['email'],
				password=serializer.validated_data['password'],
				user_type='OWNER',
<<<<<<< HEAD
				country=serializer.validated_data['country'],				
				user_timezone=serializer.validated_data['timezone'],
				last_name=serializer.validated_data['last_name'],
				first_name=serializer.validated_data['first_name'],
=======
				country=serializer.validated_datap['country'],				
				user_timezone=serializer.validated_datap['timezone'],
				last_name=serializer.validated_datap['last_name'],
				first_name=serializer.validated_datap['first_name'],
>>>>>>> main
			)
		except (ValidationError, EmailSendException):
			raise

		return Response({
		'email': pending_user.email,
		'is_link_social': is_link_social,
		'detail': message,
	}, status=status.HTTP_201_CREATED)


class CustomerRegisterView(APIView):
	permission_classes = [AllowAny]
	
	def post(self, request):
		serializer = CustomerSignupSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		
		try:
			pending_user, is_link_social, message = UserRegistrationService.register_pending_user(
				email=serializer.validated_data['email'],
				password=serializer.validated_data['password'],
				user_type='OWNER',
<<<<<<< HEAD
				country=serializer.validated_data['country'],				
				user_timezone=serializer.validated_data['timezone'],
				last_name=serializer.validated_data['last_name'],
				first_name=serializer.validated_data['first_name'],		
=======
				country=serializer.validated_datap['country'],				
				user_timezone=serializer.validated_datap['timezone'],
				last_name=serializer.validated_datap['last_name'],
				first_name=serializer.validated_datap['first_name'],		
>>>>>>> main
			)
		except (ValidationError, EmailSendException):
			raise
		
		return Response({
		'detail': message,
		'email': pending_user.email,
		'is_link_social': is_link_social,
	}, status=status.HTTP_201_CREATED)


<<<<<<< HEAD
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

=======
class VerifyEmailView(APIView):
	permission_classes = [AllowAny]

	def get(self, token):

		try:
			user, is_link_social, message  = UserRegistrationService.verify_and_activate(token)
		except (NotFound, ValidationError):
			raise

>>>>>>> main
		refresh = RefreshToken.for_user(user)
		access_token = str(refresh.access_token)
		refresh_token = str(refresh)
		
		serializer = UserSerializer(user, fields=['id', 'email', 'first_name', 'last_name', 'user_type' 'progress'])

		response_data = {
      'detail': message,
      'user': serializer.data,
      'is_link_social': is_link_social
    }

		status = status.HTTP_201_CREATED

		return self.create_token_response(access_token, refresh_token, response_data, status, platform)

<<<<<<< HEAD
=======
		return Response({
			'message': message,
			'user': serializer.data,
			'is_link_social': is_link_social,
			'refresh': str(refresh),
			'access': str(refresh.access_token),
		})
>>>>>>> main

class ResendVerificationEmailView(APIView):
	permission_classes = [AllowAny]

	"""確認メール再送信"""
	def post(self, request):
		rate_limiter = AuthRateLimiter()
		ip = self.get_client_ip(request)
			
		if not rate_limiter.check_email_resend_limit(ip):
			remaining_time = rate_limiter.get_email_resend_reset_time(
				f"auth:register:{ip}"
			)
			raise Throttled(
				detail=_('試行回数が多すぎます。%(remaining_time)s秒後に再試行してください') % {
					'remaining_time': remaining_time
				}
			)
		email = request.data.get('email')

		try:
			UserRegistrationService.resend_verification_email(email)
		except (NotFound, EmailSendException):
			raise
		
<<<<<<< HEAD
		return Response(
			{'detail': _('確認メールを再送信しました')},
			status=status.HTTP_200_OK
    )
=======
		return Response({ 'message': _('確認メールを再送信しました') })
>>>>>>> main

class ChangePendingEmailView(APIView):
	permission_classes = [AllowAny]

	"""仮登録中のメールアドレス変更"""
	def post(self, request):
		rate_limiter = AuthRateLimiter()
		ip = self.get_client_ip(request)
			
		if not rate_limiter.check_email_resend_limit(ip):
			remaining_time = rate_limiter.get_email_resend_reset_time(
				f"auth:register:{ip}"
			)
			raise Throttled(
				detail=_('試行回数が多すぎます。%(remaining_time)s秒後に再試行してください') % {
					'remaining_time': remaining_time
				}
			)
		
		old_email = request.data.get('old_email')
		new_email = request.data.get('new_email')
		
		try:
			pending_user = UserRegistrationService.change_pending_email(old_email, new_email)
		except (NotFound, EmailSendException):
			raise

		return Response({
<<<<<<< HEAD
			'detail': _('%(new_email)s に確認メールを送信しました')%{'new_email':new_email},
=======
			'message': _('%(new_email)s に確認メールを送信しました')%{'new_email':new_email},
>>>>>>> main
			'email': pending_user.email,
		},status=status.HTTP_200_OK)