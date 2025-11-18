from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.core.cache import cache
from django.core.exceptions import ValidationError

# from authentication.serializers import ActivationSerializer
from users.serializers import UserSerializer
from ..services import UserRegistrationService


class ActivateAPIView(APIView):
	permission_classes = [AllowAny]
	
	def post(self, request):
		
		# serializer = ActivationSerializer(data=request.data)
		if not serializer.is_valid():
			return Response( serializer.errors, status=status.HTTP_400_BAD_REQUEST)
		data = serializer.validated_data
		session_token = data.get('session_token')
		user_type = data.get('user_type')
		
		try:
			user, refresh, message = UserRegistrationService.register_user(session_token, user_type, data)
			serializer = UserSerializer(user, fields=['id', 'email', 'progress'])
		except ValidationError as e:
			return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

		tokens = None
		if refresh:
			tokens = {'refresh': str(refresh), 'access': str(refresh.access_token),}

		return Response(
			{ 'message': message, 'user': serializer.data, 'tokens': tokens,}, 
			status=status.HTTP_201_CREATED
		)
    