from django.utils import timezone
from django.db import models


# === セキュリティ関連メソッド ===
class SecurityMixin:

  """アカウントロック状態チェック"""
  def is_account_locked(self):
    if self.account_locked_until:
      if self.account_locked_until > timezone.now():
        return True
      else:
        self.account_locked_until = None
        self.failed_login_attempts = 0
        self.save(update_fields=['account_locked_until', 'failed_login_attempts'])
    return False

  """ログイン失敗回数を増やし、必要に応じてロック"""
  def increment_failed_login(self):
    self.failed_login_attempts += 1
    
    if self.failed_login_attempts >= 5:
      from datetime import timedelta
      self.account_locked_until = timezone.now() + timedelta(minutes=30)
    
    self.save(update_fields=['failed_login_attempts', 'account_locked_until'])

  """ログイン成功時に失敗回数をリセット"""
  def reset_failed_login(self):
    if self.failed_login_attempts > 0 or self.account_locked_until:
      self.failed_login_attempts = 0
      self.account_locked_until = None
      self.save(update_fields=['failed_login_attempts', 'account_locked_until'])


# === permission 関連メゾット（True or False)===
class PermissionMixin:
  # === Django標準メソッド（管理画面用） ===
  """ Django標準のパーミッションチェック"""
  def has_perm(self, perm, obj=None):
    if not self.is_active:
      return False
    
    if self.is_superuser or self.is_system_admin:
      return True
    
    # permission_codeを抽出
    if '.' in perm:
      permission_code = perm.split('.')[-1]
    else:
        permission_code = perm
    
    return self.has_permission(permission_code)
  
  """複数のパーミッションをチェック"""
  def has_perms(self, perm_list, obj=None):
    return all(self.has_perm(perm, obj) for perm in perm_list)
  
  """管理画面でアプリが表示されるかどうかを判定"""
  def has_module_perms(self, app_label):
    if not self.is_active:
      return False
    
    if self.is_superuser or self.is_system_admin:
      return True
    
    if self.user_type == 'OWNER':
      return self.get_owned_companies().exists()
    
    if self.user_type == 'STAFF':
        return self.get_all_tenants().exists()
    return False
  
  # === 既存のカスタムメソッド ===
  """指定されたテナントにアクセスできるかチェック"""
  def can_access_tenant(self, tenant):
    if self.is_system_admin:
      return True
    
    if self.user_type == 'OWNER':
      from .organization import CompanyOwnership
      return CompanyOwnership.objects.filter(
        owner=self,
        company=tenant.company,
        is_active=True
      ).exists()
    
    elif self.user_type == 'STAFF':
      from .organization import TenantMembership
      return TenantMembership.objects.filter(
        user=self,
        tenant=tenant,
        is_active=True
      ).exists()
    
    elif self.user_type == 'CUSTOMER':
      # TODO: Customer
      return False
    
    return False
  
  """指定されたCompanyにアクセスできるかチェック"""
  def can_access_company(self, company):
    if self.is_system_admin:
      return True
    
    if self.user_type == 'OWNER':
      from .organization import CompanyOwnership
      return CompanyOwnership.objects.filter(
        owner=self,
        company=company,
        is_active=True
      ).exists()
    elif self.user_type == 'STAFF':
      staff_tenants = self.get_all_tenants()
      return staff_tenants.filter(company=company).exists()
    
    return False
  

  """ユーザーが特定の権限を持っているかチェック"""
  """Args:permission_code, Returns:bool"""
  def has_permission(self, permission_code, tenant=None):
    if self.is_system_admin:
      return True
    
    if self.user_type == 'OWNER':
      if tenant:
        return self.can_access_company(tenant.company)
      return False
    
    #For staff
    from core.models import UserRole, RolePermission
    now = timezone.now()
    # 有効なロールを取得
    role_query = UserRole.objects.filter(
      user=self,
      role__is_active=True,
      valid_from__lte=now
    ).filter(
      models.Q(valid_until__isnull=True) | models.Q(valid_until__gte=now)
    )
        
    if tenant:
      role_query = role_query.filter(role__tenant=tenant)
    
    valid_role_ids = role_query.values_list('role_id', flat=True)
      
    has_perm = RolePermission.objects.filter(
      role_id__in=valid_role_ids,
      permission__code=permission_code,
      permission__is_active=True
    ).exists()
    
    return has_perm

  
  """ユーザーが持つすべての権限コードを取得"""
  """Args:tenant:  Returns:list: """
  def get_all_permissions(self, tenant=None):
    from core.models import Permission, UserRole, RolePermission
    
    #For Admin
    if self.is_system_admin:
        return list(Permission.objects.filter(
            is_active=True
        ).values_list('code', flat=True))
    
    #For Owner
    if self.user_type == 'OWNER':
      if tenant and self.can_access_company(tenant.company):
        return list(Permission.objects.filter(
          is_active=True
        ).values_list('code', flat=True))
      elif not tenant and self.get_owned_companies().exists():
        return list(Permission.objects.filter(
          is_active=True
        ).values_list('code', flat=True))
      return []
    
    #For Staff
    now = timezone.now()
    role_query = UserRole.objects.filter(
      user=self,
      role__is_active=True,
      valid_from__lte=now
    ).filter(
      models.Q(valid_until__isnull=True) | models.Q(valid_until__gte=now)
    )
    
    if tenant:
      role_query = role_query.filter(role__tenant=tenant)
    
    valid_role_ids = role_query.values_list('role_id', flat=True)
    
    permissions = Permission.objects.filter(
      permission_roles__role_id__in=valid_role_ids,
      is_active=True
    ).distinct().values_list('code', flat=True)
    
    return list(permissions)
  
  """カテゴリごとに権限を整理して取得"""
  """Args:tenant:  Returns:dict:"""
  def permissions_by_cat(self, tenant=None):
    from collections import defaultdict
    permission_list = self.permissions(tenant=tenant)

    result = defaultdict(list)
    for perm in permission_list:
        result[perm.category].append(perm.code)

    return dict(result)
  
  """すべてのテナントごとに権限を取得"""
  """Returns:dict:"""
  def get_permissions_for_all_tenants(self):
    result = {}
    for tenant in self.get_all_tenants():
      result[tenant] = {
          'permissions': self.get_all_permissions(tenant),
          'permissions_by_category': self.get_permissions_by_category(tenant),
          'membership': self.get_tenant_membership(tenant) if self.user_type == 'STAFF' else None
      }
    return result
  
  """ユーザーがアクセスできるユーザーを取得"""
  """Args:tenant(filter, option) Returns:QuerySet:"""  
  def get_accessible_users(self, tenant=None):
    model = self.__class__
    if self.is_system_admin:
      if tenant:
        return model.objects.filter(
          tenant_memberships__tenant=tenant,
          tenant_memberships__is_active=True
        ).distinct()
      return model.objects.all()
    
    if self.user_type == 'OWNER':
      companies = self.get_owned_companies()

      #For specific tenant filter
      if tenant:
        if tenant.company in companies:
          return model.objects.filter(
            tenant_memberships__tenant=tenant,
            tenant_memberships__is_active=True
          ).distinct()
        return model.objects.none()
        
      #For all tenant
      from .organization import Tenant
      tenants = Tenant.objects.filter(company__in=companies, is_active=True)
      return model.objects.filter(
          tenant_memberships__tenant__in=tenants,
          tenant_memberships__is_active=True
      ).distinct()
      
    # スタッフは同じテナントのユーザー
    if self.user_type == 'STAFF':
      accessible_tenants = self.get_all_tenants()
      if tenant:
        #For specific tenant
        if tenant in accessible_tenants:
          return model.objects.filter(
            tenant_memberships__tenant=tenant,
            tenant_memberships__is_active=True
          ).distinct()
        return model.objects.none()
      
      #For all tenant(所属しているテナントに限る)
      return model.objects.filter(
        tenant_memberships__tenant__in=accessible_tenants,
        tenant_memberships__is_active=True
      ).distinct()
    
    return None
    
  # === デバッグ用メソッド ===
  """ 権限情報のサマリーを取得（デバッグ用）"""  
  #! 後で確認
  def get_permission_summary(self):
    summary = {
      'user_type': self.get_user_type_display(),
      'is_system_admin': self.is_system_admin,
      'accessible_tenants_count': self.get_all_tenants().count(),
    }
    
    if self.user_type == 'OWNER':
      summary['owned_companies'] = [c.name for c in self.get_owned_companies()]
    elif self.user_type == 'STAFF':
      summary['all_tenants'] = [t.name for t in self.get_all_tenants()]
    
    # 各テナントでの権限
    summary['permissions_by_tenant'] = {}
    for tenant in self.get_all_tenants()[:5]:  # 最初の5件のみ
        summary['permissions_by_tenant'][tenant.name] = {
            'count': len(self.get_all_permissions(tenant)),
            'categories': list(self.get_permissions_by_category(tenant).keys())
        }
    
    return summary