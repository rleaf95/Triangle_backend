from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from users.serializers import UserSerializer

class TokenResponseMixin:
  def create_token_response(self, user, message, is_link_social, platform='web', ):

    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    refresh_token = str(refresh)
    
    serializer = UserSerializer(user, fields=['id', 'email', 'first_name', 'last_name', 'progress'])

    response_data = {
      'message': message,
      'user': serializer.data,
      'is_link_social': is_link_social
    }
    
    if platform in ['ios', 'android']:
      response_data['access'] = access_token
      response_data['refresh'] = refresh_token
      response = Response(response_data, status=status.HTTP_201_CREATED)
    else:
      response = Response(response_data, status=status.HTTP_201_CREATED)
      response.set_cookie(
        key='access_token',
        value=access_token,
        httponly=True,
        secure=False,
        samesite='Strict',
        max_age=900,
      )
      response.set_cookie(
        key='refresh_token',
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite='Strict',
        max_age=86400,
      )

    return response