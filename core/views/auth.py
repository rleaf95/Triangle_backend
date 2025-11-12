from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.core.cache import cache
from django.core.exceptions import ValidationError
from allauth.account.utils import send_email_confirmation
from rest_framework_simplejwt.tokens import RefreshToken
from allauth.account.models import EmailConfirmation

from ..serializers.auth import SignupSerializer, EmailConfirmSerializer, SocialLoginSerializer
from apps.accounts.services import UserRegistrationService
from apps.accounts.models import StaffInvitation


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

		except ValidationError as e:
			return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
		
		if refresh is None:
			send_email_confirmation(request, user, signup=True)

		tokens = None
		if refresh:
			tokens = {
				'refresh': str(refresh),
				'access': str(refresh.access_token),
			}

		return Response({
			'message': message,
			'user': {
					'id': user.id,
					'email': user.email,
					'first_name': user.first_name,
					'last_name': user.last_name,
			},
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
			user.is_active = True
			user.save()
			
			refresh = RefreshToken.for_user(user)
			
			return Response({
				'message': 'メールアドレスが確認されました',
				'user': {
					'id': user.id,
					'email': user.email,
					'first_name': user.first_name,
					'last_name': user.last_name,
				},
				'tokens': {
					'refresh': str(refresh),
					'access': str(refresh.access_token),
				}
			}, status=status.HTTP_200_OK)
				
		except EmailConfirmation.DoesNotExist:
			return Response({'error': '無効な確認キーです'}, status=status.HTTP_400_BAD_REQUEST)


class SocialLoginAPIView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = SocialLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        session_token = data.get('session_token')
        provider = data['provider']
        access_token = data['access_token']
        
        # 追加情報フォームからの送信かどうか
        is_completing_signup = data.get('is_completing_signup', False)
        
        try:
            social_user_data = self._get_social_user_data(provider, access_token)
            
            if session_token:
                # STAFF登録
                return self._handle_staff_social_login(
                    session_token,
                    provider,
                    social_user_data,
                    is_completing_signup,
                    data
                )
            else:
                # CUSTOMER登録/ログイン
                return self._handle_customer_social_login(
                    provider,
                    social_user_data,
                    is_completing_signup,
                    data
                )
                
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    # _get_social_user_data, _get_google_user_data等は変更なし
    
    def _handle_staff_social_login(self, session_token, provider, social_user_data, is_completing_signup, form_data):
        """
        STAFFのソーシャルログイン処理
        
        招待トークンがある場合は、必ず追加情報フォームを要求
        """
        # Redisからセッションデータを取得
        cache_key = f'invitation_session:{session_token}'
        session_data = cache.get(cache_key)
        
        if not session_data:
            return Response(
                {'error': 'セッションが無効または期限切れです'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 招待を取得
        try:
            invitation = StaffInvitation.objects.get(id=session_data['invitation_id'])
        except StaffInvitation.DoesNotExist:
            cache.delete(cache_key)
            return Response(
                {'error': '招待情報が見つかりません'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 使用済みチェック
        if invitation.is_used:
            cache.delete(cache_key)
            return Response(
                {'error': 'この招待は既に使用されています'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # トークン一致チェック
        if invitation.token != session_data['invitation_token']:
            cache.delete(cache_key)
            return Response(
                {'error': '招待情報が改ざんされています'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 追加情報が必要かチェック
        needs_additional_info = self._check_staff_needs_additional_info(
            social_user_data,
            invitation
        )
        
        if needs_additional_info and not is_completing_signup:
            # 追加情報が必要な場合、一時データをRedisに保存
            temp_key = f'social_signup_temp:{session_token}:{provider}'
            cache.set(temp_key, {
                'provider': provider,
                'social_user_data': social_user_data,
                'session_token': session_token,
                'invitation_id': invitation.id
            }, timeout=600)  # 10分間有効
            
            return Response({
                'requires_additional_info': True,
                'temp_token': temp_key,
                'prefilled_data': {
                    'email': social_user_data.get('email', ''),
                    'first_name': social_user_data.get('given_name', ''),
                    'last_name': social_user_data.get('family_name', ''),
                },
                'missing_fields': self._get_missing_fields(social_user_data, invitation)
            }, status=status.HTTP_206_PARTIAL_CONTENT)
        
        # 追加情報フォームから送信された場合、または追加情報が不要な場合
        if is_completing_signup:
            # フォームデータで不足情報を補完
            social_user_data.update({
                'given_name': form_data.get('first_name', social_user_data.get('given_name', '')),
                'family_name': form_data.get('last_name', social_user_data.get('family_name', '')),
                'email': form_data.get('email', social_user_data.get('email', ''))
            })
        
        # STAFFをアクティベート
        user = SocialLoginService.activate_staff_with_social(
            invitation=invitation,
            provider=provider,
            provider_user_id=social_user_data['id'],
            email=social_user_data['email'],
            first_name=social_user_data.get('given_name', ''),
            last_name=social_user_data.get('family_name', ''),
            picture=social_user_data.get('picture', '')
        )
        
        # Redisから削除
        cache.delete(cache_key)
        if is_completing_signup:
            temp_key = form_data.get('temp_token')
            if temp_key:
                cache.delete(temp_key)
        
        # JWTトークン発行
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'message': 'スタッフアカウントがアクティベートされました',
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'user_type': user.user_type
            },
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_200_OK)
    
    def _handle_customer_social_login(self, provider, social_user_data, is_completing_signup, form_data):
        """
        CUSTOMERのソーシャルログイン処理
        
        既存ユーザーの場合は直接ログイン
        新規ユーザーで情報が不足している場合は追加フォームを要求
        """
        # 既存ユーザーかチェック
        existing_user = SocialLoginService.find_existing_user(
            provider=provider,
            provider_user_id=social_user_data['id'],
            email=social_user_data.get('email')
        )
        
        if existing_user:
            # 既存ユーザーは直接ログイン
            refresh = RefreshToken.for_user(existing_user)
            
            return Response({
                'message': 'ログインに成功しました',
                'user': {
                    'id': existing_user.id,
                    'email': existing_user.email,
                    'first_name': existing_user.first_name,
                    'last_name': existing_user.last_name,
                    'user_type': existing_user.user_type
                },
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }, status=status.HTTP_200_OK)
        
        # 新規ユーザーの場合、追加情報が必要かチェック
        needs_additional_info = self._check_customer_needs_additional_info(social_user_data)
        
        if needs_additional_info and not is_completing_signup:
            # 一時データを保存
            temp_key = f'social_signup_temp:customer:{provider}:{social_user_data["id"]}'
            cache.set(temp_key, {
                'provider': provider,
                'social_user_data': social_user_data
            }, timeout=600)
            
            return Response({
                'requires_additional_info': True,
                'temp_token': temp_key,
                'prefilled_data': {
                    'email': social_user_data.get('email', ''),
                    'first_name': social_user_data.get('given_name', ''),
                    'last_name': social_user_data.get('family_name', ''),
                },
                'missing_fields': self._get_missing_fields(social_user_data)
            }, status=status.HTTP_206_PARTIAL_CONTENT)
        
        # 追加情報フォームから送信された場合、または追加情報が不要な場合
        if is_completing_signup:
            social_user_data.update({
                'given_name': form_data.get('first_name', social_user_data.get('given_name', '')),
                'family_name': form_data.get('last_name', social_user_data.get('family_name', '')),
                'email': form_data.get('email', social_user_data.get('email', ''))
            })
        
        # ユーザー作成
        user = SocialLoginService.get_or_create_user(
            provider=provider,
            provider_user_id=social_user_data['id'],
            email=social_user_data['email'],
            first_name=social_user_data.get('given_name', ''),
            last_name=social_user_data.get('family_name', ''),
            picture=social_user_data.get('picture', '')
        )
        
        # 一時データ削除
        if is_completing_signup:
            temp_key = form_data.get('temp_token')
            if temp_key:
                cache.delete(temp_key)
        
        # JWTトークン発行
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'message': '登録が完了しました',
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'user_type': user.user_type
            },
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)
    
    def _check_staff_needs_additional_info(self, social_user_data, invitation):
        """
        STAFFに追加情報が必要かチェック
        
        招待トークンがある場合は常に追加情報を要求
        （セキュリティ上、ユーザーに確認させる）
        """
        # 招待の場合は常にTrue（ユーザーに確認させる）
        return True
    
    def _check_customer_needs_additional_info(self, social_user_data):
        """
        CUSTOMERに追加情報が必要かチェック
        
        メールアドレスまたは名前が不足している場合True
        """
        email = social_user_data.get('email', '').strip()
        first_name = social_user_data.get('given_name', '').strip()
        last_name = social_user_data.get('family_name', '').strip()
        
        # メールアドレスが必須
        if not email:
            return True
        
        # 名前が両方とも空の場合
        if not first_name and not last_name:
            return True
        
        return False
    
    def _get_missing_fields(self, social_user_data, invitation=None):
        """不足しているフィールドのリストを返す"""
        missing = []
        
        if not social_user_data.get('email'):
            missing.append('email')
        if not social_user_data.get('given_name'):
            missing.append('first_name')
        if not social_user_data.get('family_name'):
            missing.append('last_name')
        
        return missing