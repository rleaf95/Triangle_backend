from django.db import models
from django.db.models import Q, Count, Prefetch

# ========================================
# Company関連のQuerySet
# ========================================
class CompanyQuerySet(models.QuerySet):
  """Companyモデル用のカスタムQuerySet"""
  
  def active(self):
    """アクティブな会社のみ"""
    return self.filter(is_active=True)
  
  # === オーナー関連 ===
  def owned_by(self, user):
    """特定のユーザーが所有する会社"""
    return self.filter(
      ownerships__owner=user,
      ownerships__is_active=True,
      is_active=True
    ).distinct()
  
  def with_owner(self, owner):
    """特定のオーナーを持つ会社（エイリアス）"""
    return self.owned_by(owner)
  
  # === テナント関連 ===
  def with_tenants(self):
    """テナント数を含める"""
    return self.annotate(
      tenant_count=Count('tenants', filter=Q(tenants__is_active=True))
    )
  
  def has_active_tenants(self):
    """アクティブなテナントを持つ会社のみ"""
    return self.filter(
      tenants__is_active=True
    ).distinct()
  
  # === アクセス制御 ===
  def accessible_by(self, user):
    """ユーザーがアクセス可能な会社"""
    if user.is_system_admin:
      return self.active()
    
    if user.user_type == 'OWNER':
      return self.owned_by(user)
    
    if user.user_type == 'STAFF':
      # スタッフが所属するテナントの会社
      return self.filter(
        tenants__memberships__user=user,
        tenants__memberships__is_active=True,
        is_active=True
      ).distinct()
    
    return self.none()
  
  # === 検索 ===
  def search(self, query):
    """会社を検索"""
    if not query:
      return self
    return self.filter(name__icontains=query)
  
  # === パフォーマンス最適化 ===
  def with_tenants_prefetch(self):
    """テナント情報をプリフェッチ"""
    from ..models import Tenant
    return self.prefetch_related(
      Prefetch(
        'tenants',
        queryset=Tenant.objects.filter(is_active=True)
      )
    )

  def with_owners_prefetch(self):
    """オーナー情報をプリフェッチ"""
    return self.prefetch_related('ownerships__owner')


class CompanyManager(models.Manager):
  """Companyモデル用のカスタムManager"""
  
  def get_queryset(self):
    return CompanyQuerySet(self.model, using=self._db)
  
  def active(self):
    return self.get_queryset().active()
  
  def owned_by(self, user):
    return self.get_queryset().owned_by(user)
  
  def accessible_by(self, user):
    return self.get_queryset().accessible_by(user)
  
  def search(self, query):
    return self.get_queryset().search(query)


# ========================================
# Tenant関連のQuerySet
# ========================================
class TenantQuerySet(models.QuerySet):
  """Tenantモデル用のカスタムQuerySet"""
  
  # === 基本フィルタ ===
  def active(self):
    """アクティブなテナントのみ"""
    return self.filter(is_active=True)
  
  # === 会社関連 ===
  def in_company(self, company):
    """特定の会社に所属するテナント"""
    return self.filter(company=company)
  
  def in_companies(self, companies):
    """複数の会社に所属するテナント"""
    return self.filter(company__in=companies)
  
  def of_owner(self, owner):
    """特定のオーナーが所有する会社のテナント"""
    return self.filter(
      company__ownerships__owner=owner,
      company__ownerships__is_active=True,
      is_active=True
    ).distinct()
  
  # === メンバー関連 ===
  def with_member(self, user):
    """特定のユーザーがメンバーとして所属するテナント"""
    return self.filter(
      memberships__user=user,
      memberships__is_active=True,
      is_active=True
    ).distinct()
  
  def with_members_count(self):
    """メンバー数を含める"""
    return self.annotate(
      member_count=Count(
        'memberships',
        filter=Q(memberships__is_active=True)
      )
    )
  
  def has_members(self):
    """メンバーがいるテナントのみ"""
    return self.filter(
      memberships__is_active=True
    ).distinct()
    
  # === アクセス制御 ===
  def accessible_by(self, user):
    from ..models import Company
    """ユーザーがアクセス可能なテナント"""
    if user.is_system_admin:
        return self.active()
    
    if user.user_type == 'OWNER':
      companies = Company.objects.owned_by(user)
      return self.filter(
        company__in=companies,
        is_active=True
      )
    
    if user.user_type == 'STAFF':
      return self.filter(
        memberships__user=user,
        memberships__is_active=True,
        is_active=True
      ).distinct()
    
    return self.none()
  
  # === 検索 ===
  def search(self, query):
    """テナントを検索"""
    if not query:
      return self
    return self.filter(
      Q(name__icontains=query) |
      Q(company__name__icontains=query)
    )
    
  # === パフォーマンス最適化 ===
  def with_company_info(self):
    """会社情報を含める"""
    return self.select_related('company')
  
  def with_members_prefetch(self):
    """メンバー情報をプリフェッチ"""
    return self.prefetch_related(
      'memberships__user'
    ).annotate(
      member_count=Count(
        'memberships',
        filter=Q(memberships__is_active=True)
      )
    )
  
  def with_full_info(self):
    """全ての関連情報を含める"""
    return self.select_related('company') \
      .prefetch_related('memberships__user') \
      .with_members_count()


class TenantManager(models.Manager):
    """Tenantモデル用のカスタムManager"""
    
    def get_queryset(self):
      return TenantQuerySet(self.model, using=self._db)
    
    def active(self):
      return self.get_queryset().active()
    
    def in_company(self, company):
      return self.get_queryset().in_company(company)
    
    def of_owner(self, owner):
      return self.get_queryset().of_owner(owner)
    
    def with_member(self, user):
      return self.get_queryset().with_member(user)
    
    def accessible_by(self, user):
      return self.get_queryset().accessible_by(user)
    
    def search(self, query):
      return self.get_queryset().search(query)