from django.db import models
from django.utils import timezone
import uuid
from datetime import timedelta
from organizations.models import Tenant
from users.models import User

class StaffInvitationQuerySet(models.QuerySet):
  def with_related_info(self):
    """関連情報を含めてプリフェッチ"""
    return self.select_related(
      'user',
      'tenant__company',
      'tenant',
      'invited_by'
    )
  
  def valid(self):
    """有効な招待のみ（未使用 & 期限内）"""
    return self.filter(
      is_used=False,
      expires_at__gt=timezone.now()
    )
  def by_id(self, id):
    return self.filter(id=id)
  
  def by_token(self, token):
    """トークンで検索"""
    return self.filter(token=token)
  
  def by_email(self, email):
    """メールアドレスで検索"""
    return self.filter(email=email)
  
  def for_tenant(self, tenant):
    """特定のテナントの招待"""
    return self.filter(tenant=tenant)
  
  def sent_by(self, user):
    """特定のユーザーが送信した招待"""
    return self.filter(invited_by=user)
  
  def used(self):
    """使用済みの招待"""
    return self.filter(is_used=True)
  
  def unused(self):
    """未使用の招待"""
    return self.filter(is_used=False)
  
  def expired(self):
    """期限切れの招待"""
    return self.filter(expires_at__lte=timezone.now())

class StaffInvitationManager(models.Manager):
  """StaffInvitationモデル用のカスタムManager"""
  
  def get_queryset(self):
    return StaffInvitationQuerySet(self.model, using=self._db)
  
  # QuerySetのメソッドをManagerレベルでも使えるようにする
  def with_related_info(self):
    return self.get_queryset().with_related_info()
  
  def valid(self):
    return self.get_queryset().valid()
  
  def by_token(self, token):
    return self.get_queryset().by_token(token)
  
  def by_email(self, email):
    return self.get_queryset().by_email(email)
  
  def for_tenant(self, tenant):
    return self.get_queryset().for_tenant(tenant)
  
  def sent_by(self, user):
    return self.get_queryset().sent_by(user)
  
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
  TIMEZONE_CHOICES = (
    ('Asia/Tokyo', '日本標準時 (JST)'),
    ('Australia/Sydney', 'オーストラリア東部標準時 (AEST) - シドニー'),
    ('Australia/Melbourne', 'オーストラリア東部標準時 (AEST) - メルボルン'),
    ('Australia/Brisbane', 'オーストラリア東部標準時 (AEST) - ブリスベン'),
    ('Australia/Perth', 'オーストラリア西部標準時 (AWST) - パース'),
    ('Australia/Adelaide', 'オーストラリア中部標準時 (ACST) - アデレード'),
  )
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  token = models.CharField('招待トークン', max_length=64, unique=True, db_index=True)
  
  invited_by = models.ForeignKey(
    User,
    on_delete=models.CASCADE,
    related_name='sent_invitations',
    limit_choices_to={'user_type': 'OWNER'}
  )
  tenant = models.ForeignKey(
    Tenant,
    on_delete=models.CASCADE,
    related_name='staff_invitations'
  )
  # 招待先情報
  user = models.ForeignKey(
    User,
    on_delete=models.CASCADE,
    related_name='invited',
    limit_choices_to={'user_type': 'OWNER'}
  )
  email = models.EmailField('招待メールアドレス')
  first_name = models.CharField('名', max_length=50, blank=True)
  last_name = models.CharField('姓', max_length=50, blank=True)
  language = models.CharField('言語', max_length=10, default='en', choices=LANGUAGE_CHOICES,)
  country = models.CharField('国', max_length=2, choices=COUNTRY_CHOICES)
  timezone = models.CharField('Timezone', max_length=30, choices=TIMEZONE_CHOICES)

  
  # 招待状態
  is_used = models.BooleanField('使用済み', default=False)
    
  # 日時
  created_at = models.DateTimeField('作成日時', auto_now_add=True)
  expires_at = models.DateTimeField('有効期限')
  used_at = models.DateTimeField('使用日時', null=True, blank=True)
  
  objects = StaffInvitationManager()

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