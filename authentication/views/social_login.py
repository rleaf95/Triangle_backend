import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.core.cache import cache

from ..serializers import SocialLoginSerializer
from users.serializers import UserSerializer
from ..services import SocialLoginService

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
			user, refresh, message = SocialLoginService.get_or_create_user(
				user_type, access_token, provider, session_token, id_token
			)
			
			serializer = UserSerializer(
				user, 
				fields=['id', 'email', 'first_name', 'last_name', 'progress']
			)

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