from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.core.cache import cache
import secrets

from ..serializers.auth import ValidateInvitationSerializer
from ..services.user_registration_service import UserRegistrationService


class ValidateInvitationAPIView(APIView):
  permission_classes = [AllowAny]
  
  def post(self, request):
    serializer = ValidateInvitationSerializer(data=request.data)
    if not serializer.is_valid():
      return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
      )
    
    invitation_token = serializer.validated_data['token']
    
    try:
      invitation = UserRegistrationService.validate_invitation(invitation_token)
      session_token = secrets.token_urlsafe(32)
      
      # Redisに保存（15分間有効）
      cache_key = f'invitation_session:{session_token}'
      cache.set(cache_key, {
        'invitation_id': invitation.id,
        'invitation_token': invitation_token,
        'email': invitation.email,
      }, timeout=900)
      
      return Response({
        'session_token': session_token,
        'email': invitation.email,
        'expires_in': 900,
        'message': '招待が確認されました'
      }, status=status.HTTP_200_OK)
        
    except Exception as e:
      return Response( {'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)