import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
# from django.core.cache import cache
from rest_framework_simplejwt.tokens import RefreshToken
from authentication.utils import AuthRateLimiter
from rest_framework.exceptions import Throttled

from ..serializers import OwnerSignupSerializer, CustomerSignupSerializer, EmailConfirmSerializer
from users.serializers import UserSerializer
from ..services import UserRegistrationService
from rest_framework.exceptions import ValidationError, NotFound
from common.service import EmailSendException
from django.utils.translation import gettext as _


class OwnerRegisterView(APIView):
	permission_classes = [AllowAny]
	
	def post(self, request):
		rate_limiter = AuthRateLimiter()
		ip = self.get_client_ip(request)
			
		if not rate_limiter.check_register_limit(ip):
			remaining_time = rate_limiter.get_register_reset_time(
				f"auth:register:{ip}"
			)
			raise Throttled(
    detail=_('試行回数が多すぎます。%(remaining_time)s秒後に再試行してください') % {
      'remaining_time': remaining_time
    }
  )
		
		serializer = OwnerSignupSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		try:
			pending_user, is_link_social, message = UserRegistrationService.register_pending_user(
				email=serializer.validated_data['email'],
				password=serializer.validated_data['password'],
				user_type='OWNER',
				country=serializer.validated_datap['country'],				
				user_timezone=serializer.validated_datap['timezone'],
				last_name=serializer.validated_datap['last_name'],
				first_name=serializer.validated_datap['first_name'],
			)
		except (ValidationError, EmailSendException):
			raise

		return Response({
		'message': message,
		'email': pending_user.email,
		'is_link_social': is_link_social,
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
				country=serializer.validated_datap['country'],				
				user_timezone=serializer.validated_datap['timezone'],
				last_name=serializer.validated_datap['last_name'],
				first_name=serializer.validated_datap['first_name'],		
			)
		except (ValidationError, EmailSendException):
			raise
		
		return Response({
		'message': message,
		'email': pending_user.email,
		'is_link_social': is_link_social,
	}, status=status.HTTP_201_CREATED)


class VerifyEmailView(APIView):
	permission_classes = [AllowAny]

	def get(self, token):

		try:
			user, is_link_social, message  = UserRegistrationService.verify_and_activate(token)
		except (NotFound, ValidationError):
			raise

		refresh = RefreshToken.for_user(user)
		serializer = UserSerializer(user, fields=['id', 'email', 'first_name', 'last_name', 'progress'])

		return Response({
			'message': message,
			'user': serializer.data,
			'is_link_social': is_link_social,
			'refresh': str(refresh),
			'access': str(refresh.access_token),
		})

class ResendVerificationEmailView(APIView):
	permission_classes = [AllowAny]

	"""確認メール再送信"""
	def post(self, request):
		email = request.data.get('email')

		try:
			UserRegistrationService.resend_verification_email(email)
		except (NotFound, EmailSendException):
			raise
		
		return Response({ 'message': _('確認メールを再送信しました') })

class ChangePendingEmailView(APIView):
	permission_classes = [AllowAny]

	"""仮登録中のメールアドレス変更"""
	def post(self, request):
		old_email = request.data.get('old_email')
		new_email = request.data.get('new_email')
		
		try:
			pending_user = UserRegistrationService.change_pending_email(old_email, new_email)
		except (NotFound, EmailSendException):
			raise

		return Response({
			'message': _('%(new_email)s に確認メールを送信しました')%{'new_email':new_email},
			'email': pending_user.email,
		})