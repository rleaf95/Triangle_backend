from django.db import models
from django.utils import timezone
import uuid
from datetime import timedelta

class StaffInvitation(models.Model):
  """スタッフ招待管理"""
  COUNTRY_CHOICES = (
    ('AU', 'Australia'),
    ('JP', 'Japan'),
  )
  LANGUAGE_CHOICES = (
    ('ja', '日本語'),
    ('en', 'English'),
  )
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  token = models.CharField('招待トークン', max_length=64, unique=True, db_index=True)
  
  invited_by = models.ForeignKey(
    'core.User',
    on_delete=models.CASCADE,
    related_name='sent_invitations',
    limit_choices_to={'user_type': 'OWNER'}
  )
  tenant = models.ForeignKey(
    'core.Campany',
    on_delete=models.CASCADE,
    related_name='staff_invitations'
  )
  tenant = models.ForeignKey(
    'core.Tenant',
    on_delete=models.CASCADE,
    related_name='staff_invitations',
    blank=True, null=True
  )
  # 招待先情報
  email = models.EmailField('招待メールアドレス')
  first_name = models.CharField('名', max_length=50, blank=True)
  last_name = models.CharField('姓', max_length=50, blank=True)
  language = models.CharField('言語', max_length=10, default='en', choices=LANGUAGE_CHOICES,)
  country = models.CharField('国', max_length=2, choices=COUNTRY_CHOICES)
  
  # 招待状態
  is_used = models.BooleanField('使用済み', default=False)
    
  # 日時
  created_at = models.DateTimeField('作成日時', auto_now_add=True)
  expires_at = models.DateTimeField('有効期限')
  used_at = models.DateTimeField('使用日時', null=True, blank=True)
    
  class Meta:
    db_table = 'staff_invitations'
    verbose_name = 'スタッフ招待'
    verbose_name_plural = 'スタッフ招待'
    indexes = [
      models.Index(fields=['token', 'is_used']),
      models.Index(fields=['email', 'is_used']),
    ]
    
  def __str__(self):
      return f"{self.email} - {self.tenant.name}"
  
  def save(self, *args, **kwargs):
    # トークン生成
    if not self.token:
      self.token = uuid.uuid4().hex
    
    # 有効期限設定（7日間）
    if not self.expires_at:
      self.expires_at = timezone.now() + timedelta(days=7)
    
    super().save(*args, **kwargs)
  
  """招待が有効かチェック"""
  def is_valid(self):
    return (
      not self.is_used and
      self.expires_at > timezone.now()
    )
  
  """招待URLを生成"""
  def get_invitation_url(self):
    from django.urls import reverse
    from django.conf import settings
    base_url = settings.FRONTEND_WEB_URL  # フロントエンドのURL
    return f"{base_url}/register/staff?token={self.token}"