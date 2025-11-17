from django.db import transaction
from django.core.exceptions import ValidationError
from django.core.exceptions import ValidationError
from django.core.cache import cache
from rest_framework_simplejwt.tokens import RefreshToken
from invitation.models import StaffInvitation
from users.models import User

class UserActivationService:
  @classmethod
  @transaction.atomic
  def activetion_user(cls, session_token, user_type, password):

    if session_token and user_type == 'STAFF':
    
      invitation = cls.get_invitation_from_session(session_token)

      user = invitation.user
      user.set_password(password)
      user.is_active = True
      user.is_email_verified = True
      user.auth_provider = 'email'

      user.save(update_fields=[
        'password', 'is_active', 'is_email_verified', 'auth_provider'
      ])

      return cls.complete_activation(user, invitation, session_token)
    
    else :
      raise ValidationError("許可されていない登録です")

  @classmethod
  def get_invitation_from_session(cls, session_token,):
    cache_key = f'invitation_session:{session_token}'
    session_data = cache.get(cache_key)

    if not session_data:
      raise ValidationError("セッションが無効または期限切れです。もう一度招待リンクからアクセスしてください。")
    
    try:
      invitation_id = session_data.get('invitation_id')
      invitation_token = session_data.get('invitation_token')
      session_email = session_data.get('email')
      
      invitation = (StaffInvitation.objects
        .valid()
        .by_token(invitation_token)
        .by_email(session_email)
        .by_id(invitation_id)
        .select_related('user__staff_progress')
        .order_by()
        .first())
      
      if not invitation:
        raise ValidationError('招待が見つかりません')
      
      return invitation
    except Exception as e:
      cache.delete(cache_key)
      raise

  @classmethod
  def complete_activation(cls, user, invitation, session_token):
    progress = user.staff_progress
    progress.step = 'profile'
    progress.save(update_fields=['step'])

    cache_key = f'invitation_session:{session_token}'
    cache.delete(cache_key)
    refresh = RefreshToken.for_user(user)
    
    from authentication.services.user_registration_service import UserRegistrationService
    UserRegistrationService.process_invitation(invitation, user)
    
    return user, refresh, 'USERをアクティベートしました'
  
  
  def validate_invitation(invitation_token):
    try:
      invitation = StaffInvitation.objects.valid().unused().by_token(invitation_token).get()
      return invitation
    except StaffInvitation.DoesNotExist:
        raise ValidationError('無効または期限切れの招待リンクです')