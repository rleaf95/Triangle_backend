from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class RoleQuerySet(models.QuerySet):
  """ロール用のカスタムQuerySet"""
  
  def active(self):
    """アクティブなロールのみ"""
    return self.filter(is_active=True)
  
  def for_tenant(self, tenant):
    """特定のテナントのロール"""
    return self.filter(tenant=tenant, is_active=True)
  
  def accessible_by_user(self, user, tenant=None):
    """
    ユーザーがアクセスできるロール
    Returns:QuerySet: アクセス可能なロール
    """
    if user.is_system_admin:
      return self.active()
    
    if user.user_type == 'OWNER':
      from .company import Company
      companies = Company.objects.owned_by(user)
      
      return self.filter(
        tenant__company__in=companies,
        tenant__is_active=True,
        is_active=True
      )
    
    if user.user_type == 'STAFF':
      if not tenant:
        raise ValueError("スタッフの場合、テナント指定が必須です")
      
      if not user.has_tenant_access(tenant):
        return self.none()
      
      return self.filter(
        tenant=tenant,
        is_active=True
      )
  
    return self.none()
  
  def with_permissions(self):
    """権限情報を事前取得（N+1問題対策）"""
    return self.prefetch_related('role_permissions__permission')


class RoleManager(models.Manager):
  """ロール用のカスタムManager"""
  
  def get_queryset(self):
    return RoleQuerySet(self.model, using=self._db)
  
  def active(self):
    return self.get_queryset().active()
  
  def for_tenant(self, tenant):
    return self.get_queryset().for_tenant(tenant)
  
  def accessible_by_user(self, user, tenant=None, company=None):
    return self.get_queryset().accessible_by_user(user, tenant, company)
  
  def with_permissions(self):
    return self.get_queryset().with_permissions()


class PermissionQuerySet(models.QuerySet):
  """権限用のカスタムQuerySet"""

  def active(self):
    """アクティブな権限のみ"""
    return self.filter(is_active=True)
  
  def by_category(self, category):
    """カテゴリで絞り込み"""
    return self.filter(category=category, is_active=True)
  
  def for_user(self, user, tenant=None, company=None):
    """
    ユーザーが持つ権限を取得
    
    Args:
      user: Userオブジェクト
      tenant: Tenantオブジェクト（スタッフの場合は必須）
    Returns:
      QuerySet: ユーザーが持つ権限
    """
    # システムアドミン: 全ての権限
    if user.is_system_admin:
      return self.active()
    
    # オーナー: 所有する会社配下のテナントに設定された全権限
    if user.user_type == 'OWNER':
      from .company import Company
      companies = Company.objects.owned_by(user)
      
      return self.filter(
        permission_roles__role__tenant__company__in=companies,
        permission_roles__role__tenant__is_active=True,
        permission_roles__role__is_active=True,
        is_active=True
      ).distinct()
    
    # スタッフ: 所属するテナントで割り当てられたロールの権限（⭐ テナント指定必須）
    if user.user_type == 'STAFF':
      if not tenant:
        raise ValueError("スタッフの場合、テナント指定が必須です")
      
      # ユーザーが所属するテナントか確認
      if not user.has_tenant_access(tenant):
        return self.none()
      
      # ユーザーに割り当てられたロールの権限を取得
      from .user_role import UserRole
      
      valid_roles = UserRole.objects.for_user_and_tenant(user, tenant).valid()
      
      return self.filter(
        permission_roles__role__in=valid_roles.values_list('role', flat=True),
        is_active=True
      ).distinct()
    
    return self.none()
  
  def for_role(self, role):
    """特定のロールが持つ権限"""
    return self.filter(
      permission_roles__role=role,
      is_active=True
    ).distinct()


class PermissionManager(models.Manager):
  """権限用のカスタムManager"""
  
  def get_queryset(self):
    return PermissionQuerySet(self.model, using=self._db)
  
  def active(self):
    return self.get_queryset().active()
  
  def by_category(self, category):
    return self.get_queryset().by_category(category)
  
  def for_user(self, user, tenant=None, company=None):
    return self.get_queryset().for_user(user, tenant, company)
  
  def for_role(self, role):
    return self.get_queryset().for_role(role)




class UserRoleQuerySet(models.QuerySet):
  """ユーザーロール用のカスタムQuerySet"""
  
  def valid(self):
    """現在有効なロール割り当てのみ"""
    now = timezone.now()
    return self.filter(
      valid_from__lte=now,
      valid_until__gte=now
    ) | self.filter(
      valid_from__lte=now,
      valid_until__isnull=True
    )
  
  def for_user(self, user):
    """特定のユーザーのロール割り当て"""
    return self.filter(user=user)
  
  def for_tenant(self, tenant):
    """特定のテナントのロール割り当て"""
    return self.filter(role__tenant=tenant, role__is_active=True)
  
  def for_user_and_tenant(self, user, tenant):
    """特定のユーザーと特定のテナントのロール割り当て"""
    return self.filter(
      user=user,
      role__tenant=tenant,
      role__is_active=True
    ).valid()
  
  def with_role_details(self):
    """ロール情報を事前取得（N+1問題対策）"""
    return self.select_related('role', 'role__tenant', 'user', 'granted_by')


class UserRoleManager(models.Manager):
  """ユーザーロール用のカスタムManager"""
  
  def get_queryset(self):
    return UserRoleQuerySet(self.model, using=self._db)
  
  def valid(self):
    return self.get_queryset().valid()
  
  def for_user(self, user):
    return self.get_queryset().for_user(user)
  
  def for_tenant(self, tenant):
    return self.get_queryset().for_tenant(tenant)
  
  def for_user_and_tenant(self, user, tenant):
    return self.get_queryset().for_user_and_tenant(user, tenant)
  
  def with_role_details(self):
    return self.get_queryset().with_role_details()
  

  
class RolePermissionQuerySet(models.QuerySet):
  """ロール権限用のカスタムQuerySet"""
  
  def for_role(self, role):
    """特定のロールの権限割り当て"""
    return self.filter(role=role)
  
  def for_permission(self, permission):
    """特定の権限のロール割り当て"""
    return self.filter(permission=permission)
  
  def for_tenant(self, tenant):
    """特定のテナントのロール権限"""
    return self.filter(role__tenant=tenant, role__is_active=True)
  
  def with_details(self):
    """詳細情報を事前取得（N+1問題対策）"""
    return self.select_related('role', 'permission', 'granted_by')


class RolePermissionManager(models.Manager):
  """ロール権限用のカスタムManager"""
  
  def get_queryset(self):
    return RolePermissionQuerySet(self.model, using=self._db)
  
  def for_role(self, role):
    return self.get_queryset().for_role(role)
  
  def for_permission(self, permission):
    return self.get_queryset().for_permission(permission)
  
  def for_tenant(self, tenant):
    return self.get_queryset().for_tenant(tenant)
  
  def with_details(self):
    return self.get_queryset().with_details()