from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny, IsAuthenticated
from users.serializers import UserSerializer
from django.utils.translation import gettext as _
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from .mixins import TokenResponseMixin
from authentication.serializers import CustomerLoginSerializer, BusinessLoginSerializer
from users.models.backends import CustomerAuthBackend, StaffOwnerAuthBackend


class CustomerLoginView(TokenResponseMixin, APIView):
  def post(self, request):
    serializer = CustomerLoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    email = serializer.validated_data['email']
    password = serializer.validated_data['password']
    platform = serializer.validated_data['platform']
    backend = CustomerAuthBackend()
    user = backend.authenticate(request, username=email, password=password)

    if not user:
      return Response({
        'error': _('メールアドレスまたはパスワードが正しくありません')
      }, status=status.HTTP_401_UNAUTHORIZED)
    
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    refresh_token = str(refresh)
		
    user_serializer = UserSerializer(user, fields=['id', 'email', 'first_name', 'last_name', 'user_type', 'progress'])

    response_data = { 
      'detail': _('ログインしました'),
      'user': user_serializer.data, 
    }
    response_status = status.HTTP_200_OK

    return self.create_token_response(access_token, refresh_token, response_data, response_status, platform)


class StaffOwnerLoginView(TokenResponseMixin, APIView):
  def post(self, request):
    serializer = BusinessLoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    email = serializer.validated_data['email']
    password = serializer.validated_data['password']
    platform = serializer.validated_data['platform']
    backend = StaffOwnerAuthBackend()
    user = backend.authenticate(request, username=email, password=password)
    
    if not user:
      return Response({
        'error': _('メールアドレスまたはパスワードが正しくありません')
      }, status=status.HTTP_401_UNAUTHORIZED)
    
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    refresh_token = str(refresh)
		
    user_serializer = UserSerializer(user, fields=['id', 'email', 'first_name', 'last_name', 'user_type', 'progress'])


    response_data = { 
      'detail': _('ログインしました'),
      'user': user_serializer.data, 
    }
    response_status = status.HTTP_200_OK

    return self.create_token_response(access_token, refresh_token, response_data, response_status, platform)
  

class CurrentUserView(APIView):
  permission_classes = [IsAuthenticated]
  
  def get(self, request):
    user = request.user
    serializer = UserSerializer(user, fields=['id', 'email', 'first_name', 'last_name', 'user_type', 'progress'])
    return Response({
      'user': serializer.data,
    })


class RefreshTokenView(TokenResponseMixin, APIView):
  permission_classes = [AllowAny]

  @method_decorator(ensure_csrf_cookie) 
  def post(self, request):
    platform = self.get_platform(request)
    if platform != 'web':
      refresh_token = request.get('refresh_token')
    else:
      refresh_token = request.COOKIES.get('refresh_token')
    
    
    if not refresh_token:
      return Response(
        {'detail': _('リフレッシュトークンがありません')},
        status=status.HTTP_401_UNAUTHORIZED
      )
    
    try:
      refresh = RefreshToken(refresh_token)
      access_token = str(refresh.access_token)
      
      response_data = {
        'detail': _('トークンを更新しました')
      }
      status = status.HTTP_200_OK
      
      return self.create_token_response(access_token, refresh_token, response_data, status, platform)
        
    except Exception as e:
      return Response(
        {'detail': _('トークンが無効です')},
        status=status.HTTP_401_UNAUTHORIZED
      )