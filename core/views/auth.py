import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.core.cache import cache
from django.core.exceptions import ValidationError
from allauth.account.utils import send_email_confirmation
from rest_framework_simplejwt.tokens import RefreshToken
from allauth.account.models import EmailConfirmation, EmailAddress

from ..serializers import SignupSerializer, EmailConfirmSerializer, SocialLoginSerializer, UserSerializer
from ..services import UserRegistrationService,SocialLoginService


class SignupAPIView(APIView):
	permission_classes = [AllowAny]
	
	def post(self, request):
		# バリデーション
		serializer = SignupSerializer(data=request.data)
		if not serializer.is_valid():
			return Response(
				serializer.errors,
				status=status.HTTP_400_BAD_REQUEST
			)
		data = serializer.validated_data
		session_token = data.get('session_token')
		user_type = data.get('user_type')
		
		profile_data = {
			'address': data.get('address', ''),
			'suburb': data.get('suburb', ''),
			'state': data.get('state', ''),
			'post_code': data.get('post_code', ''),
		}

		try:
			user, refresh, message = UserRegistrationService.register_user(session_token, user_type, data, profile_data)
			serializer = UserSerializer(user, fields=['id', 'email', 'first_name', 'last_name', 'progress'])
		except ValidationError as e:
			return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
		
		if refresh is None:
			send_email_confirmation(request, user, signup=True, email=user.email)

		tokens = None
		if refresh:
			tokens = {
				'refresh': str(refresh),
				'access': str(refresh.access_token),
			}

		return Response({
			'message': message,
			'user': serializer.data,
			'tokens': tokens,
		}, status=status.HTTP_201_CREATED)
    
class EmailConfirmAPIView(APIView):
	permission_classes = [AllowAny]
	
	def post(self, request):
		serializer = EmailConfirmSerializer(data=request.data)
		if not serializer.is_valid():
			return Response( serializer.errors, status=status.HTTP_400_BAD_REQUEST)
		key = serializer.validated_data['key']
		try:
			emailconfirmation = EmailConfirmation.objects.get(key=key)
			emailconfirmation.confirm(request)
			user = emailconfirmation.email_address.user
			user.is_email_verified
			user.save()

			refresh = RefreshToken.for_user(user)

			serializer = UserSerializer(user, fields=['id', 'email', 'first_name', 'last_name', 'progress'])

			return Response({
				'message': 'メールアドレスが確認されました',
				'user': serializer.data,
				'tokens': {
					'refresh': str(refresh),
					'access': str(refresh.access_token),
				}
			}, status=status.HTTP_200_OK)
				
		except EmailConfirmation.DoesNotExist:
			return Response({'error': '無効な確認キーです'}, status=status.HTTP_400_BAD_REQUEST)

class ResendEmailConfirmationView(APIView):
	permission_classes = [IsAuthenticated]
	
	def post(self, request):
		user = request.user
		
		email_address = EmailAddress.objects.filter(user=user, email=user.email, verified=False).first()
		if not email_address:
			if user.is_email_verified:
				return Response({'message': 'このメールアドレスは既に確認済みです'},status=status.HTTP_200_OK)
		
		send_email_confirmation(request, user, signup=False)
		
		return Response( {'message': 'メール認証リンクを再送信しました'}, status=status.HTTP_200_OK)

class SocialLoginAPIView(APIView):
	permission_classes = [AllowAny]
	
	def post(self, request):
		serializer = SocialLoginSerializer(data=request.data)
		if not serializer.is_valid():
			return Response( serializer.errors, status=status.HTTP_400_BAD_REQUEST)
		
		data = serializer.validated_data
		session_token = data.get('session_token')
		provider = data['provider']
		access_token = data['access_token']
		user_type = data['user_type']
		id_token = data['id_token']

		try:
			user, refresh, message = SocialLoginService.get_or_create_user(user_type, access_token, provider, session_token, id_token)
			serializer = UserSerializer(user, fields=['id', 'email', 'first_name', 'last_name', 'progress'])

			return Response({
				'message': message,
				'user': serializer.data,
				'tokens': {
					'refresh': str(refresh),
					'access': str(refresh.access_token),
				}
			}, status=status.HTTP_200_OK)
		except Exception as e:
			return Response( {'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)