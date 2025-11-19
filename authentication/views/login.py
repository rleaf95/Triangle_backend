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
  

# class LoginView(APIView):
#     permission_classes = [AllowAny]
    
#     @method_decorator(ensure_csrf_cookie)
#     def post(self, request):
#         email = request.data.get('email')
#         password = request.data.get('password')
        
#         if not email or not password:
#             return Response(
#                 {'detail': 'メールアドレスとパスワードが必要です'},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
        
#         # ユーザー認証
#         user = authenticate(request, username=email, password=password)
        
#         if user is None:
#             return Response(
#                 {'detail': '認証情報が正しくありません'},
#                 status=status.HTTP_401_UNAUTHORIZED
#             )
        
#         # JWTトークンを生成
#         refresh = RefreshToken.for_user(user)
#         access_token = str(refresh.access_token)
#         refresh_token = str(refresh)
        
#         # レスポンスを作成
#         response = Response({
#             'detail': 'ログインに成功しました',
#             'user': {
#                 'id': user.id,
#                 'email': user.email,
#                 'username': user.username,
#             }
#         }, status=status.HTTP_200_OK)
        
#         # HttpOnly Cookieにトークンを設定
#         response.set_cookie(
#             key='access_token',
#             value=access_token,
#             httponly=True,
#             secure=False,  # 開発環境ではFalse、本番環境ではTrue
#             samesite='Lax',
#             max_age=3600,  # 1時間
#         )
        
#         response.set_cookie(
#             key='refresh_token',
#             value=refresh_token,
#             httponly=True,
#             secure=False,
#             samesite='Lax',
#             max_age=86400 * 7,  # 7日間
#         )
        
#         return response


# class LogoutView(APIView):
#     permission_classes = [IsAuthenticated]
    
#     def post(self, request):
#         response = Response({
#             'detail': 'ログアウトしました'
#         }, status=status.HTTP_200_OK)
        
#         # Cookieを削除
#         response.delete_cookie('access_token')
#         response.delete_cookie('refresh_token')
        
#         return response


# class RefreshTokenView(APIView):
#     permission_classes = [AllowAny]
    
#     def post(self, request):
#         refresh_token = request.COOKIES.get('refresh_token')
        
#         if not refresh_token:
#             return Response(
#                 {'detail': 'リフレッシュトークンがありません'},
#                 status=status.HTTP_401_UNAUTHORIZED
#             )
        
#         try:
#             refresh = RefreshToken(refresh_token)
#             access_token = str(refresh.access_token)
            
#             response = Response({
#                 'detail': 'トークンを更新しました'
#             }, status=status.HTTP_200_OK)
            
#             response.set_cookie(
#                 key='access_token',
#                 value=access_token,
#                 httponly=True,
#                 secure=False,
#                 samesite='Lax',
#                 max_age=3600,
#             )
            
#             return response
            
#         except Exception as e:
#             return Response(
#                 {'detail': 'トークンが無効です'},
#                 status=status.HTTP_401_UNAUTHORIZED
#             )