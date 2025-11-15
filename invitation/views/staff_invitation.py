from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.core.cache import cache
import secrets

from invitation.serializers import ValidateInvitationSerializer
from authentication.services import  RegistrationUtilsService


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
      invitation = RegistrationUtilsService.validate_invitation(invitation_token)
      session_token = secrets.token_urlsafe(32)
      
      # Redisに保存（15分間有効）
      cache_key = f'invitation_session:{session_token}'
      cache.set(cache_key, {
        'invitation_id': invitation.id,
        'invitation_token': invitation_token,
        'email': invitation.email,
        'first_name': invitation.first_name,
        'last_name' : invitation.last_name,
        'company' : invitation.tenant.company.name,
        'tenant' : invitation.tenant.name,
      }, timeout=900)
      
      return Response({ 
        'session_token': session_token, 
        'email': invitation.email, 
        'first_name': invitation.first_name,
        'last_name' : invitation.last_name,
        'company' : invitation.tenant.company.name,
        'tenant' : invitation.tenant.name,
        'expires_in': 900, 
        'message': '招待が確認されました' 
      },status=status.HTTP_200_OK)
        
    except Exception as e:
      return Response( {'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)