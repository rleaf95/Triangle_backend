from django.db import models
from django.db.models import Q
from django.utils import timezone
from .organization_querysets import CompanyQuerySet

# ========================================
# User関連のQuerySet
# ========================================
class UserQuerySet(models.QuerySet):
  # === 基本的なフィルタメソッド ===
  def active(self):
    return self.filter(is_active=True)
  
  def by_user_type(self, user_type):
    return self.filter(user_type=user_type)
  
  def system_admins(self):
    return self.filter(is_system_admin=True)
  
  def owners(self):
    return self.by_user_type('OWNER')
  
  def staff(self):
    return self.by_user_type('STAFF')

  def customers(self):
    return self.by_user_type('CUSTOMER')
  
  def by_email(self, email):
    return self.filter(email=email)
  def find_by_email(self, email):
    return self.by_email(email).first()
  
  # === ソーシャルログイン関連のメソッド ===
  def by_google_id(self, google_user_id):
    """GoogleユーザーIDで検索"""
    return self.filter(google_user_id=google_user_id)
  
  def by_facebook_id(self, facebook_user_id):
    """FacebookユーザーIDで検索"""
    return self.filter(facebook_user_id=facebook_user_id)
  
  def by_social_id(self, provider, social_user_id):
    """ソーシャルプロバイダーIDで検索"""
    field_name = f'{provider}_user_id'
    return self.filter(**{field_name: social_user_id})
  def find_by_social_id(self, provider, social_user_id):
    return self.by_social_id(provider, social_user_id).first()
  
  def social_login_users(self):
    """ソーシャルログインユーザーのみ"""
    return self.filter(
      models.Q(google_user_id__isnull=False) |
      models.Q(facebook_user_id__isnull=False) |
      models.Q(line_user_id__isnull=False)
    )
  
  def email_login_users(self):
    """メール/パスワードログインユーザーのみ"""
    return self.filter(auth_provider='email')
  
  # === テナント・会社関連のフィルタ ===
  def in_tenant(self, tenant):
    """特定のテナントに所属するユーザー"""
    return self.filter(
      tenant_memberships__tenant=tenant,
      tenant_memberships__is_active=True
    ).distinct()
  
  def in_tenants(self, tenants):
    """複数のテナントに所属するユーザー"""
    return self.filter(
      tenant_memberships__tenant__in=tenants,
      tenant_memberships__is_active=True
    ).distinct()
  
  def in_company(self, company):
    """特定の会社のテナントに所属するユーザー"""
    from .organization import Tenant
    tenants = Tenant.objects.filter(company=company, is_active=True)
    return self.in_tenants(tenants)
  
  def in_companies(self, companies):
    """複数の会社のテナントに所属するユーザー"""
    from organization import Tenant
    tenants = Tenant.objects.filter(company__in=companies, is_active=True)
    return self.in_tenants(tenants)
  
  def own_company(self, company):
    """特定のカンパニーを所持しているオーナー"""
    return self.filter(
      company_ownership__company=company,
      company_ownership__is_active=True
		).distinct()
  
	
  def owned_by_companies(self, company):
    """特定のcompanyに所属している全ユーザー"""
    owners = self.own_company(company)
    staff = self.in_company(company)
    return (owners | staff).distinct()
  

  # === UserAccessのフィルタ ===
  def accessible_by(self, requesting_user, tenant=None):
    """
    指定されたユーザーがアクセス可能なユーザーを返す
    Returns: アクセス可能なユーザーのQuerySet
    """
    if requesting_user.is_system_admin:
      if tenant:
        return self.in_tenant(tenant)
      return self.all()
    if requesting_user.user_type == 'OWNER':
      return self._accessible_by_owner(requesting_user, tenant)
    if requesting_user.user_type == 'STAFF':
      return self._accessible_by_staff(requesting_user, tenant)
    return self.none()
  
  def _accessible_by_owner(self, owner, tenant):
    """オーナーがアクセス可能なユーザー"""
    from organization import Company
    companies = Company.objects.owned_by(owner)
    if tenant:
      if tenant.company in companies:
        return self.in_tenant(tenant)
      return self.none()
    
    return self.in_companies(companies)
  
  def _accessible_by_staff(self, staff, tenant):
    """スタッフがアクセス可能なユーザー"""
    from organization import Tenant
    accessible_tenants = Tenant.objects.with_membrt(staff)
    
    if tenant:
      if tenant in accessible_tenants:
        return self.in_tenant(tenant)
      return self.none()
    
    # 所属している全テナントの場合
    return self.in_tenants(accessible_tenants)

  # === 検索関連のメソッド ===
  def search(self, query):
    """ユーザーを検索"""
    if not query:
      return self
    
    return self.filter(
      Q(id__icontains=query) |
      Q(email__icontains=query) |
      Q(first_name__icontains=query) |
      Q(last_name__icontains=query)
    )
  
  # === パフォーマンス最適化用メソッド ===
  def with_tenant_info(self):
    """テナント情報を含めてプリフェッチ"""
    return self.prefetch_related(
      'tenant_memberships__tenant',
      'tenant_memberships__tenant__company'
    )
  
  def with_role_info(self):
    """ロール情報を含めてプリフェッチ"""
    return self.prefetch_related(
      'user_roles__role__permission_roles__permission'
    )
  
  def with_full_info(self):
    """全ての関連情報を含めてプリフェッチ"""
    return self.select_related(
      'profile'
    ).prefetch_related(
      'tenant_memberships__tenant__company',
      'user_roles__role__permission_roles__permission',
      'ownerships__company'
    )


class UserManager(models.Manager):
  def get_queryset(self):
    """デフォルトのQuerySetをUserQuerySetに置き換え"""
    return UserQuerySet(self.model, using=self._db)
  
  def active(self):
    return self.get_queryset().active()
  
  def by_user_type(self, user_type):
    return self.get_queryset().by_user_type(user_type)
  
  def system_admins(self):
    return self.get_queryset().system_admins()
  
  def owners(self):
    return self.get_queryset().owners()
  
  def staff(self):
    return self.get_queryset().staff()
  
  def customers(self):
    return self.get_queryset().customers()
  
  def by_email(self, email):
    return self.get_queryset().by_email(email)
  def find_by_email(self, email):
    return self.get_queryset().find_by_email(email)
  
  def in_tenant(self, tenant):
    return self.get_queryset().in_tenant(tenant)
  
  def in_tenants(self, tenants):
    return self.get_queryset().in_tenants(tenants)
  
  def in_company(self, company):
    return self.get_queryset().in_company(company)
  
  def in_companies(self, companies):
    return self.get_queryset().in_companies(companies)
  
  def accessible_by(self, requesting_user, tenant=None):
    return self.get_queryset().accessible_by(requesting_user, tenant)
  
  def search(self, query):
    return self.get_queryset().search(query)
  
  # === ソーシャルログイン関連のメソッド ===
  def by_google_id(self, google_user_id):
    return self.get_queryset().by_google_id(google_user_id)
  
  def by_facebook_id(self, facebook_user_id):
    return self.get_queryset().by_facebook_id(facebook_user_id)
  
  def by_social_id(self, provider, social_user_id):
    return self.get_queryset().by_social_id(provider, social_user_id)
  def find_by_social_id(self, provider, social_user_id):
    return self.get_queryset().find_by_social_id(provider, social_user_id)
  

  # === 特定のユーザーを取得するメソッド ===
  
  def create_user(self, email, password=None, **extra_fields):
    """通常のユーザーを作成"""
    if not email:
      raise ValueError('メールアドレスは必須です')
    
    email = self.normalize_email(email)
    user = self.model(email=email, **extra_fields)
    user.set_password(password)
    user.save(using=self._db)
    return user
  
  def create_superuser(self, email, password=None, **extra_fields):
    """スーパーユーザーを作成"""
    extra_fields.setdefault('is_staff', True)
    extra_fields.setdefault('is_superuser', True)
    extra_fields.setdefault('is_active', True)
    extra_fields.setdefault('is_system_admin', True)
    extra_fields.setdefault('user_type', 'OWNER')
    extra_fields.setdefault('is_email_verified', True)
    
    if extra_fields.get('is_staff') is not True:
      raise ValueError('スーパーユーザーのis_staffはTrueである必要があります')
    if extra_fields.get('is_superuser') is not True:
      raise ValueError('スーパーユーザーのis_superuserはTrueである必要があります')
    
    return self.create_user(email, password, **extra_fields)
    
