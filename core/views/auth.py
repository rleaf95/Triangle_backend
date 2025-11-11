from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from google.oauth2 import id_token
from google.auth.transport import requests
from django.conf import settings
from ..models import User
from ..serializers import (
    UserSerializer,
    UserDetailSerializer,
    UserRegistrationSerializer,
    EmailLoginSerializer,
)
from ..services.social_login_service import SocialLoginService
from ..services.profile_service import ProfileService
import jwt
from jwt import PyJWKClient


class GoogleLoginAPIView(APIView):
    """ネイティブアプリ用Googleログイン"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Googleログイン
        Request Body:
            - id_token: GoogleのIDトークン（必須）
            - platform: 'ios' or 'android'（必須）
            - registration_type: 'owner' or 'customer'（新規登録時のみ）
            - invitation_token: 招待トークン（スタッフ登録時のみ）
        """
        id_token_str = request.data.get('id_token')
        platform = request.data.get('platform', 'android')
        registration_type = request.data.get('registration_type')
        invitation_token = request.data.get('invitation_token')
        
        if not id_token_str:
            return Response(
                {'error': 'id_tokenは必須です'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # プラットフォームに応じたクライアントID
            if platform == 'ios':
                client_id = settings.GOOGLE_IOS_CLIENT_ID
            else:
                client_id = settings.GOOGLE_ANDROID_CLIENT_ID
            
            # Googleトークンを検証
            idinfo = id_token.verify_oauth2_token(
                id_token_str,
                requests.Request(),
                client_id
            )
            
            if idinfo['aud'] not in [client_id, settings.GOOGLE_OAUTH2_CLIENT_ID]:
                raise ValueError('Invalid audience')
            
            # ユーザー情報取得
            email = idinfo['email']
            google_user_id = idinfo['sub']
            first_name = idinfo.get('given_name', '')
            last_name = idinfo.get('family_name', '')
            picture = idinfo.get('picture', '')
            
            # ソーシャルログインサービスでユーザー作成
            user, created, action = SocialLoginService.get_or_create_user(
                email=email,
                social_user_id=google_user_id,
                provider='google',
                first_name=first_name,
                last_name=last_name,
                picture=picture,
                invitation_token=invitation_token,
                registration_type=registration_type
            )
            
            # プロファイル完成度チェック
            completion_status = ProfileService.get_profile_completion_status(user)
            
            # JWTトークン生成
            refresh = RefreshToken.for_user(user)
            
            # レスポンスメッセージ
            if action == 'found_by_social_id':
                message = 'ログインしました'
            elif action == 'found_by_email':
                message = 'Googleアカウントを紐付けました'
            else:  # created
                message = '新規登録しました'
            
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserSerializer(user, context={'request': request}).data,
                'is_new_user': created,
                'action': action,
                'message': message,
                'needs_profile_completion': not completion_status['is_complete'],
                'missing_fields': completion_status['missing_fields'],
                'completion_rate': completion_status['completion_rate'],
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response(
                {'error': f'無効なトークンです: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'認証エラー: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AppleLoginAPIView(APIView):
    """ネイティブアプリ用Apple Sign In"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Apple Sign In
        
        Request Body:
            - identity_token: AppleのIDトークン（必須）
            - user: Apple User ID（必須）
            - full_name: {'givenName': '太郎', 'familyName': '山田'}（初回のみ）
            - registration_type: 'owner' or 'customer'（新規登録時のみ）
            - invitation_token: 招待トークン（スタッフ登録時のみ）
        """
        identity_token = request.data.get('identity_token')
        user_identifier = request.data.get('user')
        registration_type = request.data.get('registration_type')
        invitation_token = request.data.get('invitation_token')
        
        if not identity_token:
            return Response(
                {'error': 'identity_tokenは必須です'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Apple IDトークンを検証
            jwks_client = PyJWKClient('https://appleid.apple.com/auth/keys')
            signing_key = jwks_client.get_signing_key_from_jwt(identity_token)
            
            decoded = jwt.decode(
                identity_token,
                signing_key.key,
                algorithms=['RS256'],
                audience=settings.APPLE_CLIENT_ID,
                issuer='https://appleid.apple.com'
            )
            
            email = decoded.get('email')
            apple_user_id = decoded['sub']
            
            # 初回ログインの場合のみ名前情報が取得可能
            full_name = request.data.get('full_name', {})
            first_name = full_name.get('givenName', '')
            last_name = full_name.get('familyName', '')
            
            # メールアドレスの処理
            user_email = email or f'{apple_user_id}@privaterelay.appleid.com'
            
            # ソーシャルログインサービスでユーザー作成
            user, created, action = SocialLoginService.get_or_create_user(
                email=user_email,
                social_user_id=apple_user_id,
                provider='apple',
                first_name=first_name,
                last_name=last_name,
                picture='',
                invitation_token=invitation_token,
                registration_type=registration_type
            )
            
            # プロファイル完成度チェック
            completion_status = ProfileService.get_profile_completion_status(user)
            
            # JWTトークン生成
            refresh = RefreshToken.for_user(user)
            
            # レスポンスメッセージ
            if action == 'found_by_social_id':
                message = 'ログインしました'
            elif action == 'found_by_email':
                message = 'Appleアカウントを紐付けました'
            else:  # created
                message = '新規登録しました'
            
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserSerializer(user, context={'request': request}).data,
                'is_new_user': created,
                'action': action,
                'message': message,
                'is_private_email': not email,
                'needs_profile_completion': not completion_status['is_complete'],
                'missing_fields': completion_status['missing_fields'],
                'completion_rate': completion_status['completion_rate'],
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'認証に失敗しました: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )


class EmailRegistrationAPIView(APIView):
    """メール登録"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        メール登録
        
        Request Body:
            - email: メールアドレス（必須）
            - password: パスワード（必須、8文字以上）
            - password_confirm: パスワード確認（必須）
            - user_type: 'OWNER' or 'CUSTOMER'（必須）
            - language: 'ja' or 'en'（オプション、デフォルト: ja）
            - first_name: 名（オプション）
            - last_name: 姓（オプション）
            - invitation_token: 招待トークン（スタッフ登録時のみ）
        """
        serializer = UserRegistrationSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            user = serializer.save()
            
            # プロファイル完成度チェック
            completion_status = ProfileService.get_profile_completion_status(user)
            
            # JWTトークン生成
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserSerializer(user, context={'request': request}).data,
                'message': '登録が完了しました',
                'needs_profile_completion': not completion_status['is_complete'],
                'missing_fields': completion_status['missing_fields'],
                'completion_rate': completion_status['completion_rate'],
            }, status=status.HTTP_201_CREATED)
        
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class EmailLoginAPIView(APIView):
    """メールログイン"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        メールログイン
        
        Request Body:
            - email: メールアドレス（必須）
            - password: パスワード（必須）
        """
        serializer = EmailLoginSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # JWTトークン生成
            refresh = RefreshToken.for_user(user)
            
            # プロファイル完成度チェック
            completion_status = ProfileService.get_profile_completion_status(user)
            
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserSerializer(user, context={'request': request}).data,
                'message': 'ログインしました',
                'needs_profile_completion': not completion_status['is_complete'],
                'missing_fields': completion_status['missing_fields'],
                'completion_rate': completion_status['completion_rate'],
            }, status=status.HTTP_200_OK)
        
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class TokenRefreshAPIView(APIView):
    """トークンリフレッシュ"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        アクセストークンをリフレッシュ
        
        Request Body:
            - refresh: リフレッシュトークン（必須）
        """
        refresh_token = request.data.get('refresh')
        
        if not refresh_token:
            return Response(
                {'error': 'refreshトークンは必須です'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            refresh = RefreshToken(refresh_token)
            
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),  # ローテーション後の新しいリフレッシュトークン
            }, status=status.HTTP_200_OK)
        except TokenError as e:
            return Response(
                {'error': '無効なトークンです'},
                status=status.HTTP_401_UNAUTHORIZED
            )


class LogoutAPIView(APIView):
    """ログアウト"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        ログアウト（トークンをブラックリストに追加）
        
        Request Body:
            - refresh: リフレッシュトークン（必須）
        """
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            return Response(
                {'message': 'ログアウトしました'},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'error': 'ログアウトに失敗しました'},
                status=status.HTTP_400_BAD_REQUEST
            )