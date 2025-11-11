# core/adapters/allauth_adapters.py
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.core.exceptions import ValidationError
from core.services.user_registration_service import UserRegistrationService
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from core.services.social_login_service import SocialLoginService


class CustomAccountAdapter(DefaultAccountAdapter):
  """メール登録用アダプター"""
  
  def is_open_for_signup(self, request):
    """新規登録を許可するか"""
    invitation_token = request.session.get('staff_invitation_token')
    user_type =request.session.get('user_type')

    if user_type:
      if invitation_token:
        try:
          UserRegistrationService.validate_invitation(invitation_token)
          return True
        except ValidationError:
          return False
      return True
    else:
      user_type = 'CUSTOMER'
      return True
    
    

  def save_user(self, request, user, form, commit=True):
    """新規作成(STAFFはActivate)"""
    invitation_token = request.session.get('staff_invitation_token')
    user_type = request.session.get('user_type', 'CUSTOMER')
    
    invitation = None
    if invitation_token:
      try:
        invitation = UserRegistrationService.validate_invitation(invitation_token)
      except ValidationError:
        invitation = None
    
    validated_user_type = UserRegistrationService.validate_user_type(user_type, invitation)
    
    # プロフィールデータを抽出
    profile_data = {}
    for field in ['address', 'suburb', 'state', 'post_code']:
      if field in form.cleaned_data:
        profile_data[field] = form.cleaned_data[field]
    
    try:
      if validated_user_type == 'STAFF' and invitation:
        if hasattr(invitation, 'user') and invitation.user:
          user_data = self._extract_user_data_from_form(form, user)
          registered_user = UserRegistrationService.activate_staff_user(invitation=invitation, user_data=user_data, profile_data=profile_data )
          del request.session['staff_invitation_token']
          del request.session['user_type']
          return registered_user
        else:
          raise ValidationError("招待にユーザー情報が含まれていません")
      
      user = super().save_user(request, user, form, commit=False)
      registered_user = UserRegistrationService.complete_user_registration(user=user, validated_user_type=validated_user_type, invitation=invitation, profile_data=profile_data )
      
      if 'staff_invitation_token' in request.session:
        del request.session['staff_invitation_token']
      if 'user_type' in request.session:
        del request.session['user_type']
      
      return registered_user
        
    except ValidationError as e:
      raise
    
  def _extract_user_data_from_form(self, form, user):
    """フォームからユーザーデータを抽出"""
    return {
      'email': user.email,
      'first_name': form.cleaned_data.get('first_name', ''),
      'last_name': form.cleaned_data.get('last_name', ''),
      'phone_number': form.cleaned_data.get('phone_number'),
      'user_type': form.cleaned_data.get('user_type', 'CUSTOMER'),
      'language': form.cleaned_data.get('language', 'ja'),
      'country': form.cleaned_data.get('country', 'AU'),
      'timezone': form.cleaned_data.get('timezone'),
      'picture': form.cleaned_data.get('picture'),
      'password': user.password if hasattr(user, 'password') else None,
      'auth_provider': 'email'
    }
    



class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
  """ソーシャルログイン用のカスタムAdapter"""
  def is_auto_signup_allowed(self, request):
    invitation_token = request.session.get('staff_invitation_token')
    user_type = request.session.get('user_type', 'CUSTOMER')
    if user_type:
      if invitation_token:
        return False
      return True
    else:
      user_type = 'CUSTOMER'
      return True
  
  def save_user(self, request, sociallogin, form=None):
    invitation_token = request.session.get('staff_invitation_token')
    user_type = request.session.get('user_type', 'CUSTOMER')

    if not user_type:
      user_type = 'CUSTOMER'
    
    invitation = None
    if invitation_token:
      try:
        invitation = UserRegistrationService.validate_invitation(invitation_token)
      except ValidationError:
        invitation = None
    
    validated_user_type = UserRegistrationService.validate_user_type(user_type, invitation)
    
    # ソーシャルアカウント情報を取得
    provider = sociallogin.account.provider
    uid = sociallogin.account.uid
    extra_data = sociallogin.account.extra_data
    user = sociallogin.user
    
    social_data = SocialLoginService.extract_social_data(provider, extra_data)
    form_data = SocialLoginService.prepare_user_data_from_form(form)
    
    try:
      registered_user, created, message = SocialLoginService.get_or_create_user(
        validated_user_type, 
        provider, 
        uid,
        social_data,
        form_data,
        invitation,
      )
      if 'staff_invitation_token' in request.session:
        del request.session['staff_invitation_token']
      del request.session['user_type']
      return registered_user, created, message
        
    except ValidationError as e:
        raise