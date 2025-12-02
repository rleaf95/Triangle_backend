from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from users.serializers import UserSerializer

class TokenResponseMixin:
  def get_platform(self, request):
    platform = request.data.get('platform')
    
    if not platform:
      platform = request.headers.get('X-Platform')
    
    if not platform:
      user_agent = request.headers.get('User-Agent', '').lower()
      if 'android' in user_agent:
        platform = 'android'
      elif 'iphone' in user_agent or 'ipad' in user_agent:
        platform = 'ios'
      else:
        platform = 'web'
    
    return platform
  
  def create_token_response(self, access_token, refresh_token, response_data, http_status, platform='web', ):
        
    if platform in ['ios', 'android']:
      response_data['access'] = access_token
      response_data['refresh'] = refresh_token
      response = Response(response_data, status=http_status)
    else:
      response = Response(response_data, status=http_status)
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