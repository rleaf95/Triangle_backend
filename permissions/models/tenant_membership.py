from django.db import models
from organizations.models import Tenant
from django.utils import timezone


class TenantMembership(models.Model):
  tenant = models.ForeignKey( Tenant, on_delete=models.CASCADE, related_name='memberships')
  user = models.ForeignKey( 'users.User', on_delete=models.CASCADE, related_name='tenant_memberships', limit_choices_to={'user_type': 'STAFF'} )
  started_at = models.DateField('店舗スタート日', default=timezone.now)
  ended_at = models.DateField('店舗終了日', null=True, blank=True, help_text='退任・売却日')
  is_active = models.BooleanField('アクティブ', default=True)
  added_by = models.ForeignKey(
    'users.User',
    on_delete=models.SET_NULL,
    null=True,
    related_name='added_menberships',
    verbose_name='追加者'
  )
  created_at = models.DateTimeField('作成日時', auto_now_add=True)

  class Meta:
    db_table = 'tenant_memberships'
    verbose_name = 'Tenant Membership / テナント所属'
    verbose_name_plural = 'Tenant Memberships / テナント所属'
    unique_together = [['user', 'tenant']]  # 同じ組み合わせは1つだけ
    indexes = [
      models.Index(fields=['user', 'is_active']),
      models.Index(fields=['tenant', 'is_active']),
    ]
    
    def __str__(self):
      return f"{self.user.email} - {self.tenant.name}"
    
