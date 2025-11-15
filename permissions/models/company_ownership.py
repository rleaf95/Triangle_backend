from django.db import models
from organizations.models import Company
from django.utils import timezone

class CompanyOwnership(models.Model):
  company = models.ForeignKey( Company, on_delete=models.CASCADE, related_name='ownerships')
  owner = models.ForeignKey( 'users.User', on_delete=models.CASCADE, related_name='company_ownerships', limit_choices_to={'user_type': 'OWNER'} )
  
  # 期間管理
  started_at = models.DateField('開始日', default=timezone.now)
  ended_at = models.DateField('終了日', null=True, blank=True, help_text='退任・売却日')
  is_active = models.BooleanField('アクティブ', default=True)
  
  # 監査情報
  added_by = models.ForeignKey(
    'users.User',
    on_delete=models.SET_NULL,
    null=True,
    related_name='added_ownerships',
    verbose_name='追加者'
  )
  # plan = models.CharField( 'プラン', max_length=20,
  #   choices=[
  #     ('free', '無料'),
  #     ('basic', 'ベーシック'),
  #     ('premium', 'プレミアム'),
  #   ],
  #   default='basic'
  # )
  created_at = models.DateTimeField('作成日時', auto_now_add=True)
  updated_at = models.DateTimeField('更新日時', auto_now=True)
  
  class Meta:
    db_table = 'company_ownerships'
    verbose_name = 'Company Ownership'
    verbose_name_plural = 'Company Ownerships'
    unique_together = [['company', 'owner', 'started_at']]
    indexes = [
        models.Index(fields=['company', 'is_active']),
        models.Index(fields=['owner', 'is_active']),
    ]
  
  def __str__(self):
      return f"{self.owner.email} - {self.company.name}"
  
  #Todo オーナーごとの店舗アクセス規定を後で追加する
