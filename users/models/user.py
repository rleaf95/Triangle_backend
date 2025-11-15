from django.contrib.auth.models import AbstractBaseUser
from django.db import models
from django.utils import timezone
import uuid
from .mixins import SecurityMixin, PermissionMixin
from .user_querysets import UserManager

class User(AbstractBaseUser, SecurityMixin, PermissionMixin,):
  USER_TYPE_CHOICES = (
    ('OWNER', 'オーナー'),
    ('STAFF', 'スタッフ'),
    ('CUSTOMER', '顧客'),
  )
  LANGUAGE_CHOICES = (
    ('ja', '日本語'),
    ('en', 'English'),
  )
  COUNTRY_CHOICES = (
    ('AU', 'Australia'),
    ('JP', 'Japan'),
  )
  TIMEZONE_CHOICES = (
    ('Asia/Tokyo', '日本標準時 (JST)'),
    ('Australia/Sydney', 'オーストラリア東部標準時 (AEST) - シドニー'),
    ('Australia/Melbourne', 'オーストラリア東部標準時 (AEST) - メルボルン'),
    ('Australia/Brisbane', 'オーストラリア東部標準時 (AEST) - ブリスベン'),
    ('Australia/Perth', 'オーストラリア西部標準時 (AWST) - パース'),
    ('Australia/Adelaide', 'オーストラリア中部標準時 (ACST) - アデレード'),
  )
  AUTH_PROVIDER_CHOICES = (
    ('email', 'メール'),
    ('google', 'Google'),
    ('line','Line'),
    ('facebook','Facebook')
  )
    
  # === Base  ===
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, verbose_name='ユーザーID')
  google_user_id = models.CharField( 'Google User ID', max_length=255, blank=True, null=True, unique=True, db_index=True )
  line_user_id = models.CharField( 'Apple User ID', max_length=255, blank=True, null=True, unique=True, db_index=True )
  facebook_user_id = models.CharField( 'Apple User ID', max_length=255, blank=True, null=True, unique=True, db_index=True )
  email = models.EmailField( 'メールアドレス', unique=True, db_index=True, blank=True, )
  user_type = models.CharField( 'ユーザータイプ', max_length=10, choices=USER_TYPE_CHOICES)
  profile_image = models.ImageField('プロフィール画像', upload_to='profiles/', blank=True, null=True )
  profile_image_url = models.URLField( 'プロフィール画像URL', blank=True, null=True, help_text='ソーシャルログインの画像URL')
  first_name = models.CharField('名', max_length=50, blank=True)
  last_name = models.CharField('姓', max_length=50, blank=True)
  phone_number = models.CharField('電話番号', max_length=20, blank=True, null=True)

  # === User State === 
  is_active = models.BooleanField('アクティブ', default=True)
  is_staff = models.BooleanField('スタッフステータス', default=False)
  is_superuser = models.BooleanField('スーパーユーザーステータス', default=False)
  is_email_verified = models.BooleanField('メール認証済み', default=False)
  is_system_admin = models.BooleanField( 'システム管理者', default=False, help_text='開発者・運営のみ。Django管理画面にアクセス可能')
    
  # === Datetime ===
  date_joined = models.DateTimeField('登録日時', default=timezone.now)
  last_login = models.DateTimeField('最終ログイン', null=True, blank=True)
  updated_at = models.DateTimeField('更新日時', auto_now=True)

  # === カスタムUserManager ===
  objects = UserManager()

  # === セキュリティ関連 ===
  failed_login_attempts = models.IntegerField('ログイン失敗回数', default=0)
  account_locked_until = models.DateTimeField( 'アカウントロック期限', null=True, blank=True)
  password_changed_at = models.DateTimeField('パスワード変更日時', default=timezone.now )
    
  # === 認証方法 ===
  auth_provider = models.CharField( '認証プロバイダー', max_length=20, default='email', choices=AUTH_PROVIDER_CHOICES )
    
  # === 国際化設定 ===
  language = models.CharField('言語', max_length=10, choices=LANGUAGE_CHOICES, blank=True, null=True)
  country = models.CharField('国', max_length=2, choices=COUNTRY_CHOICES, blank=True, null=True )
  timezone = models.CharField('タイムゾーン', max_length=50, choices=TIMEZONE_CHOICES, blank=True, null=True)
    
  objects = UserManager()
    
  USERNAME_FIELD = 'email'
  REQUIRED_FIELDS = ['user_type']
    
  class Meta:
    db_table = 'users'
    verbose_name = 'User'
    verbose_name_plural = 'Users'
    indexes = [
      models.Index(fields=['email', 'user_type']),
      models.Index(fields=['is_active', 'user_type']),
    ]
  def __str__(self):

    if self.user_type == 'STAFF':
      from organizations.models import Tenant
      tenants = Tenant.objects.with_member(self)
      tenant_name = f"{tenants.count()}店舗に所属" if tenants.exists() else '所属なし'
    elif self.user_type == 'OWNER':
      from organizations.models import Company
      companies = Company.objects.owned_by(self)
      tenant_name = f"{companies.count()}社を経営" if companies.exists() else '会社なし'
    else:
      tenant_name = 'カスタマー'
    
    return f"{self.email} ({self.get_user_type_display()}) - {tenant_name}"

  """国固有の税務情報を取得"""
  def get_tax_info(self):
    if self.country == 'AU':
      return getattr(self, 'australian_tax_info', None)
    elif self.country == 'JP':
      return getattr(self, 'japanese_tax_info', None)
    return None
  
  """税務情報が登録されているか"""
  def has_tax_info(self):
    return self.get_tax_info() is not None


class StaffProfile(models.Model):
  user = models.OneToOneField(
    User,
    on_delete=models.CASCADE,
    related_name='staff_profile',
    limit_choices_to={'user_type': 'STAFF'}
  )
  address = models.CharField('住所', max_length=50, blank=True, null=True)
  suburb = models.CharField('Suburb/市区町村', max_length=100, blank=True)
  state = models.CharField('州/都道府県', max_length=50, blank=True, null=True)
  post_code = models.CharField('郵便番号', max_length=10, blank=True, null=True)
  hire_date = models.DateField('入社日', blank=True, null=True)
  unemployed_date = models.DateField('退職日', blank=True, null=True)
  
  class Meta:
    db_table = 'staff_profiles'
    verbose_name = 'スタッフプロファイル'
    verbose_name_plural = 'スタッフプロファイル'
  
  def __str__(self):
    name = f"{self.last_name} {self.first_name}".strip() or "名前未設定"
    return f"{name} - {self.user.email}"


class AustralianTaxInfo(models.Model):
  user = models.OneToOneField(
    User,
    on_delete=models.CASCADE,
    related_name='australian_tax_info',
    limit_choices_to={'country': 'AU'}
  )
  employment_status = models.CharField('雇用形態', max_length=20, blank=True,
    choices=[
        ('FULL_TIME', 'Full Time'),
        ('PART_TIME', 'Part Time'),
        ('CASUAL', 'Casual'),
        ('CONTRACT', 'Contract'),
    ],
  )
  taxfile_number = models.CharField('Taxfile Number', blank=True, null=True, max_length=20, )
  super_number = models.CharField('Super Number', blank=True, null=True, max_length=20, )
  latest_tax_withheld = models.DecimalField("Latest Tax Withheld",blank=True, null=True, max_digits=10, decimal_places=2)
  latest_super_amount = models.DecimalField("Latest Super Amount",blank=True, null=True, max_digits=10, decimal_places=2)
  ytd_tax = models.DecimalField("YTD Tax", max_length=9, blank=True, null=True, max_digits=10, decimal_places=2)
  ytd_super = models.DecimalField("YTD Super", max_length=20, blank=True, null=True, max_digits=10, decimal_places=2)
  last_sync = models.DateTimeField('last Sync', blank=True, null=True)

class JapaneseTaxInfo(models.Model):
  user = models.OneToOneField(
    User,
    on_delete=models.CASCADE,
    related_name='japanese_tax_info',
    limit_choices_to={'country': 'JP'}
  )

  # Depends on Free, build later

  my_number = models.CharField('マイナンバー', max_length=12, blank=True, help_text='12桁の個人番号')
  pension_number = models.CharField('基礎年金番号', max_length=20, blank=True, help_text='例: 1234-567890')
  employment_insurance_number = models.CharField( '雇用保険被保険者番号', max_length=20, blank=True )
  


# class CustomerProfile(models.Model):
#     """顧客プロファイル"""
#     user = models.OneToOneField(
#         User,
#         on_delete=models.CASCADE,
#         related_name='customer_profile'
#     )
#     first_name = models.CharField('名', max_length=50)
#     last_name = models.CharField('姓', max_length=50)
#     phone_number = models.CharField('電話番号', max_length=20, blank=True)
#     birth_date = models.DateField('生年月日', null=True, blank=True)
#     address = models.TextField('住所', blank=True)
    
#     class Meta:
#         db_table = 'customer_profiles'
#         verbose_name = '顧客プロファイル'
#         verbose_name_plural = '顧客プロファイル'
    
#     def __str__(self):
#         return f"{self.last_name} {self.first_name} - {self.user.email}"
    
#     @property
#     def full_name(self):
#         return f"{self.last_name} {self.first_name}"

class StaffRegistrationProgress(models.Model):
  user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_progress',)
  step = models.CharField(max_length=50, choices=[
    ('basic_info', '基本情報'),
    ('profile', 'プロフィール'),
    ('done', '完了'),
  ])


class CustomerRegistrationProgress(models.Model):
  user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer_progress',)
  step = models.CharField(max_length=50, choices=[
    ('basic_info', '基本情報'),
    ('detail', '詳細'),
    ('done', '完了'),
  ])
