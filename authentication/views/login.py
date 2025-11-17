from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken

class CustomerLoginView(APIView):
  def post(self, request):
    email = request.data.get('email')
    password = request.data.get('password')
    user = authenticate( request, username=email, password=password )
    
    if not user:
      return Response({
        'error': 'メールアドレスまたはパスワードが正しくありません'
      }, status=status.HTTP_401_UNAUTHORIZED)
    
    if user.user_group != 'CUSTOMER':
      return Response({
        'error': 'カスタマーアカウントでログインしてください'
      }, status=status.HTTP_403_FORBIDDEN)
    
    refresh = RefreshToken.for_user(user)
    
    return Response({
      'user': { 'id': str(user.id), 'email': user.email, 'user_type': user.user_type},
      'refresh': str(refresh),
      'access': str(refresh.access_token),
    })


class StaffOwnerLoginView(APIView):
  def post(self, request):
    email = request.data.get('email')
    password = request.data.get('password')
    
    user = authenticate(request, username=email, password=password )
    
    if not user:
      return Response({
        'error': 'メールアドレスまたはパスワードが正しくありません'
      }, status=status.HTTP_401_UNAUTHORIZED)
    
    if user.user_group != 'STAFF_OWNER':
      return Response({
        'error': 'スタッフ/オーナーアカウントでログインしてください'
      }, status=status.HTTP_403_FORBIDDEN)
    
    refresh = RefreshToken.for_user(user)
    
    return Response({
      'user': { 'id': str(user.id), 'email': user.email, 'user_type': user.user_type},
      'refresh': str(refresh),
      'access': str(refresh.access_token),
    })