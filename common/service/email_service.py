from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.core.mail import EmailMessage
from django.core.mail.backends.smtp import SMTPServerDisconnected
from smtplib import (
    SMTPException, 
    SMTPAuthenticationError, 
    SMTPConnectError,
    SMTPRecipientsRefused,
    SMTPSenderRefused
)
from socket import gaierror, timeout as SocketTimeout
import logging
email_logger = logging.getLogger('email')


class EmailSendResult:
  def __init__(self, success, error_type=None, error_message=None):
    self.success = success
    self.error_type = error_type
    self.error_message = error_message


class EmailService:
  @staticmethod
  def send_template_email(to_email, subject, html_content, text_content, logging_text):
    from django.core.mail import send_mail

    try:
      email = EmailMessage(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to_email],
      )
      email.attach_alternative(html_content, "text/html")
      email.send(fail_silently=False)
      email_logger.info(f'Success: {logging_text}: {to_email}')
      return EmailSendResult(success=True)
      
    except SMTPAuthenticationError as e:
      email_logger.error(f"SMTP authentication error: {str(e)}")
      return EmailSendResult(
        success=False,
        error_type='authentication',
        error_message='メールサーバーの認証に失敗しました'
      )
        
    except SMTPConnectError as e:
      email_logger.error(f"SMTP connection error: {str(e)}")
      return EmailSendResult(
        success=False,
        error_type='connection',
        error_message='メールサーバーに接続できませんでした'
      )
        
    except SMTPRecipientsRefused as e:
      email_logger.error(f"Recipients refused for {to_email}: {str(e)}")
      return EmailSendResult(
        success=False,
        error_type='invalid_recipient',
        error_message='メールアドレスが無効です'
      )
        
    except SMTPSenderRefused as e:
      email_logger.error(f"Sender refused: {str(e)}")
      return EmailSendResult(
        success=False,
        error_type='sender_refused',
        error_message='メール送信元が拒否されました'
      )
        
    except SMTPServerDisconnected as e:
      email_logger.error(f"SMTP server disconnected: {str(e)}")
      return EmailSendResult(
        success=False,
        error_type='disconnected',
        error_message='メールサーバーとの接続が切断されました'
      )
        
    except (gaierror, SocketTimeout) as e:
      email_logger.error(f"Network error: {str(e)}")
      return EmailSendResult(
        success=False,
        error_type='network',
        error_message='ネットワークエラーが発生しました'
      )
        
    except Exception as e:
      email_logger.error(f"Unexpected error sending email to {to_email}: {str(e)}")
      return EmailSendResult(
        success=False,
        error_type='unknown',
        error_message='予期しないエラーが発生しました'
      )