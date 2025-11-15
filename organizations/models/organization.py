from django.db import models
import uuid
from.organization_querysets import CompanyManager, TenantManager

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

  #Custom Manager
  objects = CompanyManager()

  class Meta:
    db_table = 'companies'
    verbose_name = 'Company'
    verbose_name_plural = 'Companies'
  def __str__(self):
    return self.name
          


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

    #Custom Manager
    objects = TenantManager()
    
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
    