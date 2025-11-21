from django.conf import settings
from django.utils.translation import gettext as _
from django.core.mail import EmailMessage
from rest_framework import status
from rest_framework.exceptions import APIException
from smtplib import (
    SMTPException, 
    SMTPAuthenticationError, 
    SMTPConnectError,
    SMTPRecipientsRefused,
    SMTPSenderRefused,
)
from rest_framework import status
import logging
email_logger = logging.getLogger('email')


class EmailSendException(APIException):
  """メール送信エラー"""
  pass

class EmailService:
  ERROR_TEMPLATES = {
    'authentication': {
      'message': _('システムエラーが発生しました。管理者に連絡してください。'),
      'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR
    },
    'connection': {
      'message': _('メール送信に失敗しました。しばらく経ってから再度お試しください。'),
      'status_code': status.HTTP_503_SERVICE_UNAVAILABLE
    },
    'invalid_email': {
      'message': _('メールアドレスの形式が正しくありません。'),
      'status_code': status.HTTP_400_BAD_REQUEST
    },
    'recipient_refused': {
      'message': _('このメールアドレスは存在しないか、受信できません。'),
      'status_code': status.HTTP_400_BAD_REQUEST
    },
    'smtp': {
      'message': _('メール送信に失敗しました。メールアドレスをご確認ください。'),
      'status_code': status.HTTP_400_BAD_REQUEST
    },
    'unknown': {
      'message': _('メール送信に失敗しました。'),
      'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR
    }
  }

  @classmethod
  def _raise_error(cls, error_type):
    """テンプレートから例外を生成してraise"""
    error_template = cls.ERROR_TEMPLATES.get(error_type, cls.ERROR_TEMPLATES['unknown'])
    
    exception = EmailSendException(error_template['message'])
    exception.status_code = error_template['status_code']
    raise exception

  @classmethod
  def send_template_email(cls, to_email, subject, html_content, text_content, logging_text):
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
    
      return True 
      
    except SMTPAuthenticationError as e:
      email_logger.error(f'SMTP認証失敗: {to_email}, エラー: {str(e)}')
      cls._raise_error('authentication')
    
    except SMTPRecipientsRefused as e:
      email_logger.warning(f'受信者拒否: {to_email}, エラー: {str(e)}')
      cls._raise_error('recipient_refused')
    
    except SMTPConnectError as e:
      email_logger.error(f'SMTP接続失敗: {to_email}, エラー: {str(e)}')
      cls._raise_error('connection')
    
    except SMTPException as e:
      email_logger.error(f'SMTP送信失敗: {to_email}, エラー: {str(e)}')
      cls._raise_error('smtp')
    
    except Exception as e:
      email_logger.error(f'{logging_text}失敗: {to_email}, エラー: {str(e)}', exc_info=True)
      cls._raise_error('unknown')
