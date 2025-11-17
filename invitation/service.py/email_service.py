from django.conf import settings
from common.services.email_service import EmailService


class InvitationEmailService:
    """招待関連のメール送信"""
    
    @classmethod
    def send_staff_invitation(cls, invitation):
        """スタッフ招待メール"""
        invitation_url = f"{settings.FRONTEND_URL}/staff/invitation/{invitation.token}"
        
        context = {
            'email': invitation.email,
            'invitation_url': invitation_url,
            'company_name': invitation.tenant.company.name,
            'tenant_name': invitation.tenant.name,
            'invited_by': invitation.invited_by.email if invitation.invited_by else 'システム',
            'expires_at': invitation.expires_at,
        }
        
        EmailService.send_template_email(
            to_email=invitation.email,
            subject=f'{invitation.tenant.company.name} からの招待',
            template_name='emails/staff_invitation.html',
            context=context
        )