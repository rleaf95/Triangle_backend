from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone


#default(E-mail)
class CustomAccountAdapter(DefaultAccountAdapter):
  """
  カスタマー・オーナーは自由に登録可能
  スタッフは招待トークン必須
  """
  def is_open_for_signup(self, request):
    invitation_token = request.session.get('staff_invitation_token')
    if invitation_token:
      from core.models import StaffInvitation
      try:
        invitation = StaffInvitation.objects.get(
          token=invitation_token,
          is_used=False,
          expires_at__gt=timezone.now()
        )
        return True
      except StaffInvitation.DoesNotExist:
        return False

    return True
    

  """ユーザー登録時の処理"""
  def save_user(self, request, user, form, commit=True):
    user = super().save_user(request, user, form, commit=False)
    
    # 招待トークンがある場合はスタッフとして登録
    invitation_token = request.session.get('staff_invitation_token')
    if invitation_token:
      from core.models import StaffInvitation
      try:
        invitation = StaffInvitation.objects.get(
          token=invitation_token,
          is_used=False,
          expires_at__gt=timezone.now()
        )
        user.user_type = 'STAFF'
        user.language = invitation.language or 'en'
        user.country = invitation.country or 'AU'
      except StaffInvitation.DoesNotExist:
        raise ValidationError('無効な招待リンクです')
    else:
      user_type = form.cleaned_data.get('user_type', 'CUSTOMER')
      if user_type == 'STAFF':
        raise ValidationError('スタッフの登録には招待が必要です')
      
      #! formからのユーザー情報を追加する。（共通のものはifの外にまとめる）
      #! 既存ユーザーとの情報を照合する処理追加
      user.user_type = user_type
  
    if commit:
      user.save()
      if invitation_token:
        invitation.is_used = True
        invitation.registered_user = user
        invitation.used_at = timezone.now()
        invitation.save()

        del request.session['staff_invitation_token']

    return user

#Social media
class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
  """
  カスタマー・オーナーは自由に登録可能
  スタッフは招待トークン必須
  """
  def is_open_for_signup(self, request, sociallogin,):
    invitation_token = request.session.get('staff_invitation_token')
    if invitation_token:
      from core.models import StaffInvitation
      try:
        invitation = StaffInvitation.objects.get(
          token=invitation_token,
          is_used=False,
          expires_at__gt=timezone.now()
        )
        return True
      except StaffInvitation.DoesNotExist:
        return False

    return True
  
  """ソーシャルログイン前の処理"""
  def pre_social_login(self, request, sociallogin):
    # 既存ユーザーの場合はスキップ
    if sociallogin.is_existing:
      return
    # メールアドレスで既存ユーザーと紐付け
    try:
      email = sociallogin.account.extra_data.get('email')
      if email:
        from core.models import User
        user = User.objects.get(email=email)
        sociallogin.connect(request, user)
    except User.DoesNotExist:
      pass
  
  """ソーシャルログインからユーザー情報を設定"""
  def populate_user(self, request, sociallogin, data, form):
    user = super().populate_user(request, sociallogin, data)
    
    invitation_token = request.session.get('staff_invitation_token')
    if invitation_token:
      from core.models import StaffInvitation
      try:
        invitation = StaffInvitation.objects.get(
          token=invitation_token,
          is_used=False,
          expires_at__gt=timezone.now()
        )
        user.user_type = 'STAFF'
        user.language = invitation.language or 'en'
        user.country = invitation.country
      except StaffInvitation.DoesNotExist:
          raise ValidationError('無効な招待リンクです')
    else:
      user_type = form.cleaned_data.get('user_type', 'CUSTOMER')
      if user_type == 'STAFF':
        raise ValidationError('スタッフの登録には招待が必要です')
      
      #! formからのユーザー情報を追加する。（共通のものはifの外にまとめる）
      #! 既存ユーザーとの情報を照合する処理追加
      user.user_type = user_type
  
    
    user.auth_provider = sociallogin.account.provider
    
    return user
    
  """ソーシャルログインでのユーザー保存"""
  def save_user(self, request, sociallogin, form=None):
    user = super().save_user(request, sociallogin, form)
    
    invitation_token = request.session.get('staff_invitation_token')
    if invitation_token:
      from core.models import StaffInvitation
      try:
        invitation = StaffInvitation.objects.get(
            token=invitation_token,
            is_used=False
        )
        invitation.is_used = True
        invitation.registered_user = user
        invitation.used_at = timezone.now()
        invitation.save()
        del request.session['staff_invitation_token']
      except StaffInvitation.DoesNotExist:
        pass
    
    return user
