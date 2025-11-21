from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
import uuid
from .mixins import SecurityMixin
from .user_manager import UserManager
from django.core.exceptions import ValidationError


class User(AbstractBaseUser, SecurityMixin, PermissionsMixin,):
  USER_TYPE_CHOICES = (
    ('OWNER', 'オーナー'),
    ('STAFF', 'スタッフ'),
    ('CUSTOMER', '顧客'),
  )
  USER_GROUP_CHOICES = (
    ('CUSTOMER', 'カスタマー'),
    ('STAFF_OWNER', 'スタッフ/オーナー'),
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
  google_user_id = models.CharField( 'Google User ID', max_length=255, blank=True, null=True, unique=True )
  line_user_id = models.CharField( 'Line User ID', max_length=255, blank=True, null=True, unique=True )
  facebook_user_id = models.CharField( 'Facebook User ID', max_length=255, blank=True, null=True, unique=True )
  email = models.EmailField( 'メールアドレス', blank=False)
  user_type = models.CharField('ユーザータイプ', max_length=10, choices=USER_TYPE_CHOICES)
  user_group = models.CharField('ユーザーグループ', max_length=20, choices=USER_GROUP_CHOICES, editable=False )
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

  # === セキュリティ関連 ===
  failed_login_attempts = models.IntegerField('ログイン失敗回数', default=0)
  account_locked_until = models.DateTimeField( 'アカウントロック期限', null=True, blank=True)
  password_changed_at = models.DateTimeField('パスワード変更日時', default=timezone.now )
    
  # === 認証方法 ===
  auth_provider = models.CharField( '認証プロバイダー', max_length=20, default='email', choices=AUTH_PROVIDER_CHOICES )
    
  # === 国際化設定 ===
  language = models.CharField('言語', max_length=10, choices=LANGUAGE_CHOICES, blank=True, null=True)
  country = models.CharField('国', max_length=2, choices=COUNTRY_CHOICES, blank=True, null=True )
  user_timezone = models.CharField('タイムゾーン', max_length=50, choices=TIMEZONE_CHOICES, blank=True, null=True)
    
  objects = UserManager()
    
  USERNAME_FIELD = 'email'
  REQUIRED_FIELDS = ['user_type']
    
  class Meta:
    db_table = 'users'
    verbose_name = 'User'
    verbose_name_plural = 'Users'
    constraints = [ 
      models.UniqueConstraint( 
        fields=['email', 'user_group'],
        name='unique_email_user_group'
      ),
    ]
    indexes = [
      models.Index(fields=['email', 'user_group'], name='idx_email_user_group'),
      models.Index(fields=['user_type', 'is_active'], name='idx_user_type_active'),
    ]
    
  def __str__(self):
    return f"{self.email} ({self.get_user_type_display()})"
    
  def clean(self):
    """バリデーション（新規作成 + 更新時）"""
    super().clean()
    if self.user_type == 'CUSTOMER':
      existing = User.objects.filter(
        email=self.email,
        user_type='CUSTOMER'
      ).exclude(pk=self.pk)
      
      if existing.exists():
        raise ValidationError({'email': 'このメールアドレスは既に登録されています'})
    
    elif self.user_type in ['STAFF', 'OWNER']:
      existing = User.objects.filter(email=self.email, user_type__in=['STAFF', 'OWNER']).exclude(pk=self.pk)  # ← 自分を除外
      
      if existing.exists(): raise ValidationError({ 'email': 'このメールアドレスは既に登録されています'})
    
  def save(self, *args, **kwargs):
    if self.user_type == 'CUSTOMER':
        self.user_group = 'CUSTOMER'
    else:
        self.user_group = 'STAFF_OWNER'
    
    if not kwargs.pop('skip_validation', False):
        self.full_clean()
    
    super().save(*args, **kwargs)


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
