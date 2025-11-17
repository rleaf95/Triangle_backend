import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.core.cache import cache
from django.core.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
from allauth.account.models import EmailConfirmation, EmailAddress

from ..serializers import OwnerSignupSerializer, CustomerSignupSerializer, EmailConfirmSerializer
from users.serializers import UserSerializer
from ..services import UserRegistrationService


class OwnerRegisterView(APIView):
	
	def post(self, request):
		serializer = OwnerSignupSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		
		pending_user, is_link_social, message = UserRegistrationService.register_pending_user(
			email=serializer.validated_data['email'],
			password=serializer.validated_data['password'],
			user_type='OWNER',
			country=serializer.validated_datap['country'],				
			timezone=serializer.validated_datap['timezone'],				
		)
		
		return Response({
		'message': message,
		'email': pending_user.email,
		'is_link_social': is_link_social,
	}, status=status.HTTP_201_CREATED)


class CustomerRegisterView(APIView):
	
	def post(self, request):
		serializer = CustomerSignupSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		
		pending_user, is_link_social, message = UserRegistrationService.register_pending_user(
			email=serializer.validated_data['email'],
			password=serializer.validated_data['password'],
			user_type='OWNER',
			country=serializer.validated_datap['country'],				
			timezone=serializer.validated_datap['timezone'],				
		)
		
		return Response({
		'message': message,
		'email': pending_user.email,
		'is_link_social': is_link_social,
	}, status=status.HTTP_201_CREATED)


class VerifyEmailView(APIView):
	def get(self, token):

		user = UserRegistrationService.verify_and_activate(token)
		refresh = RefreshToken.for_user(user)
		serializer = UserSerializer(user, fields=['id', 'email', 'first_name', 'last_name', 'progress'])

		return Response({
				'message': '登録が完了しました',
				'user': serializer.data,
				'refresh': str(refresh),
				'access': str(refresh.access_token),
		})

class ResendVerificationEmailView(APIView):
	"""確認メール再送信"""
	def post(self, request):
		email = request.data.get('email')
		UserRegistrationService.resend_verification_email(email)
		
		return Response({
				'message': '確認メールを再送信しました'
		})

class ChangePendingEmailView(APIView):
	"""仮登録中のメールアドレス変更"""
	def post(self, request):
		old_email = request.data.get('old_email')
		new_email = request.data.get('new_email')
		
		pending_user = UserRegistrationService.change_pending_email(old_email, new_email)
		
		return Response({
			'message': f'{new_email} に確認メールを送信しました',
			'email': pending_user.email,
		})