from django.db import models
import uuid
# from .user import User
from django.utils import timezone

class Company(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  name = models.CharField('会社名', max_length=200)
  legal_name = models.CharField('法人名', max_length=200, blank=True, help_text='正式な法人名')
  abn = models.CharField('ABN', max_length=11, blank=True, help_text='オーストラリア事業者番号')
  head_office_address = models.TextField('本社住所', blank=True)
  head_office_phone = models.CharField('本社電話番号', max_length=20, blank=True)
  head_office_email = models.EmailField('本社メールアドレス', blank=True)
  is_active = models.BooleanField('アクティブ', default=True)
  created_at = models.DateTimeField('作成日時', auto_now_add=True)
  updated_at = models.DateTimeField('更新日時', auto_now=True)
  class Meta:
    db_table = 'companies'
    verbose_name = 'Company'
    verbose_name_plural = 'Companies'
  def __str__(self):
    return self.name
  
  """アクティブなオーナーを取得"""
  def get_active_owners(self):
    return 'core.User'.objects.filter(
      company_ownerships__company=self,
      company_ownerships__is_active=True
    ).distinct()

  """全店舗のスタッフを取得"""
  def get_all_staff(self):
    return 'core.User'.objects.filter(
      tenant__company=self,
      user_type='STAFF',
      is_active=True
    )
    
  """全スタッフ数"""
  def get_total_staff_count(self):
    return self.get_all_staff().count()
    
  """店舗数"""
  def get_tenant_count(self):
    return self.tenants.filter(is_active=True).count()
          


class Tenant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(
      Company,
      on_delete=models.CASCADE,
      related_name='tenants',
      verbose_name='companies'
    )
    name = models.CharField('店舗名', max_length=200)
    code = models.CharField('店舗コード', max_length=50, unique=True, help_text='例: SBY001, MEL002')
    address = models.TextField('住所')
    suburb = models.CharField('Suburb/市区町村', max_length=100, blank=True)
    state = models.CharField('州/都道府県', max_length=50)
    post_code = models.CharField('郵便番号', max_length=10)
    country = models.CharField('国', max_length=2, choices=[('AU', 'Australia'), ('JP', 'Japan')])
    
    # 連絡先
    phone_number = models.CharField('電話番号', max_length=20)
    email = models.EmailField('メールアドレス', null=True, blank=True)

    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)
    is_active = models.BooleanField('Is active', default=True)
    
    class Meta:
      db_table = 'tenants'
      verbose_name = 'Tenant'
      verbose_name_plural = 'Tenants'
      ordering = ['company', 'code']
      indexes = [
          models.Index(fields=['company', 'is_active']),
          models.Index(fields=['code']),
      ]
    
    def __str__(self):
        return f"{self.name} ({self.code}) - {self.company.name}"
    
    # def get_active_staff_count(self):
    #     """アクティブなスタッフ数を取得"""
    #     return self.users.filter(user_type='STAFF', is_active=True).count()
    
    # def get_monthly_revenue(self, year, month):
    #     """月次売上を取得（将来的に実装）"""
    #     # TODO: 売上データとの連携
    #     pass

class CompanyOwnership(models.Model):
  company = models.ForeignKey( Company, on_delete=models.CASCADE, related_name='ownerships')
  owner = models.ForeignKey( 'core.User', on_delete=models.CASCADE, related_name='company_ownerships', limit_choices_to={'user_type': 'OWNER'} )
  
  # 期間管理
  started_at = models.DateField('開始日', default=timezone.now)
  ended_at = models.DateField('終了日', null=True, blank=True, help_text='退任・売却日')
  is_active = models.BooleanField('アクティブ', default=True)
  
  # 監査情報
  added_by = models.ForeignKey(
    'core.User',
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


class TenantMembership(models.Model):
  tenant = models.ForeignKey( Tenant, on_delete=models.CASCADE, related_name='memberships')
  user = models.ForeignKey( 'core.User', on_delete=models.CASCADE, related_name='tenant_memberships', limit_choices_to={'user_type': 'STAFF'} )
  started_at = models.DateField('店舗に追加された日', default=timezone.now)
  ended_at = models.DateField('店舗終了日', null=True, blank=True, help_text='退任・売却日')
  is_active = models.BooleanField('アクティブ', default=True)
  added_by = models.ForeignKey(
    'core.User',
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
    
