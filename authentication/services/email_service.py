from django.conf import settings
from common.service import EmailService
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from django.utils.translation import get_language

class RegistrationEmailService:
  """登録関連のメール送信"""
  
  @classmethod
  def send_registration_confirmation(cls, pending_user):
    current_language = get_language() 

    verification_url = f"{settings.FRONTEND_WEB_URL}/verify/{pending_user.verification_token}"
    context = {
      'email': pending_user.email,
      'verification_url': verification_url,
      'expires_in_hours': 24,
    }

    html_content = render_to_string(f'emails/{current_language}/registration_confirmation.html', context)
    text_content = render_to_string(f'emails/{current_language}/registration_confirmation.html', context)
    
    return EmailService.send_template_email(
      to_email=pending_user.email,
      subject=_('アカウント登録の確認'),
      html_content=html_content,
      text_content=text_content,
      logging_text='Send verification mail'
    )

  @classmethod
  def resend_confirmation(cls, pending_user):
    current_language = get_language() 
    verification_url = f"{settings.FRONTEND_WEB_URL}/verify/{pending_user.verification_token}"

    context = {
      'email': pending_user.email,
      'verification_url': verification_url,
      'expires_in_hours': 24,
      'is_resend': True,
    }

    html_content = render_to_string(f'emails/{current_language}/registration_confirmation.html', context)
    text_content = render_to_string(f'emails/{current_language}/registration_confirmation.html', context)
    
    return EmailService.send_template_email(
      to_email=pending_user.email,
      subject=_('メールアドレスの確認（再送信）'),
      html_content=html_content,
      text_content=text_content,
      logging_text='Resend verification mail'
    )

    
  @classmethod
  def send_email_change_confirmation(cls, pending_user, new_email):
    current_language = get_language() 
    verification_url = f"{settings.FRONTEND_WEB_URL}/verify/{pending_user.verification_token}"
    
    context = {
      'old_email': pending_user.email,
      'new_email': new_email,
      'verification_url': verification_url,
      'expires_in_hours': 24,
    }

    html_content = render_to_string(f'emails/{current_language}/registration_confirmation.html', context)
    text_content = render_to_string(f'emails/{current_language}/registration_confirmation.html', context)
    
    return EmailService.send_template_email(
      to_email=new_email,
      subject=_('新しいメールアドレスの確認'),
      html_content=html_content,
      text_content=text_content,
      logging_text='Send verification (change)mail'
    )
