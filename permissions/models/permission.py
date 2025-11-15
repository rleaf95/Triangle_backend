from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from organizations.models import Tenant
from .permission_querysets import RolePermissionManager, RoleManager, UserRoleManager, PermissionManager

User = get_user_model()

"""ロール（役割）モデル, テナントごとに定義"""
class Role(models.Model):
  id = models.AutoField(primary_key=True)
  code = models.CharField('権限コード', max_length=100, unique=True, db_index=True)
  tenant = models.ForeignKey(
    Tenant,
    on_delete=models.CASCADE,
    related_name='roles',
    verbose_name='tenant'
  )
  name = models.CharField('Role Name', max_length=50, db_index=True)
  description = models.TextField('Description', blank=True)
  priority = models.IntegerField('Priority', default=0)
  is_active = models.BooleanField('有効', default=True)
  created_at = models.DateTimeField('作成日時', auto_now_add=True)
  updated_at = models.DateTimeField('更新日時', auto_now=True)

  objects = RoleManager()
  
  class Meta:
    db_table = 'roles'
    verbose_name = 'Role / ロール'
    verbose_name_plural = 'Roles / ロール'
    ordering = ['tenant', '-priority', 'name']
    # テナント内でロール名がユニーク
    unique_together = [['tenant', 'name']]
    indexes = [
        models.Index(fields=['tenant', 'is_active']),
  ]
  
  def __str__(self):
      return f"{self.display_name} ({self.name}) - {self.tenant.name}"

"""権限モデル全テナント共通（グローバル）"""
class Permission(models.Model):
  CATEGORY_CHOICES = [
    ('reservation', '予約管理'),
    ('pos', 'POS/販売'),
    ('inventory', '在庫管理'),
    ('staff', 'スタッフ管理'),
    ('customer', '顧客管理'),
    ('report', 'レポート'),
    ('settings', '設定'),
  ]
  id = models.AutoField(primary_key=True)
  code = models.CharField('権限コード', max_length=100, unique=True, db_index=True)
  name = models.CharField('権限名', max_length=100)
  category = models.CharField('カテゴリ', max_length=50, choices=CATEGORY_CHOICES)
  description = models.TextField('説明', blank=True)
  is_active = models.BooleanField('有効', default=True)
  created_at = models.DateTimeField('作成日時', auto_now_add=True)
  updated_at = models.DateTimeField('更新日時', auto_now=True)
  objects = PermissionManager()

  class Meta:
      db_table = 'permissions'
      verbose_name = 'Permission'
      verbose_name_plural = 'Permissions'
      ordering = ['category', 'code']
      indexes = [
          models.Index(fields=['category', 'code']),
      ]
  
  def __str__(self):
      return f"{self.name} ({self.code})"

"""ユーザーとロールの多対多関係"""
class UserRole(models.Model):
  user = models.ForeignKey(
      User,
      on_delete=models.CASCADE,
      related_name='user_roles'
  )
  role = models.ForeignKey(
      Role,
      on_delete=models.CASCADE,
      related_name='user_assignments'
  )
  valid_from = models.DateTimeField('有効開始日時', default=timezone.now)
  valid_until = models.DateTimeField('有効終了日時', null=True, blank=True)
  granted_by = models.ForeignKey(
      User,
      on_delete=models.SET_NULL,
      null=True,
      related_name='granted_roles',
      verbose_name='付与者'
  )
  granted_at = models.DateTimeField('付与日時', auto_now_add=True)
  reason = models.TextField('付与理由', blank=True)
  objects = UserRoleManager()

  
  class Meta:
    db_table = 'user_roles'
    verbose_name = 'User Role'
    verbose_name_plural = 'User Roles'
    unique_together = [['user', 'role']]
    indexes = [
      models.Index(fields=['user', 'valid_from', 'valid_until']),
    ]
  
  def __str__(self):
      return f"{self.user.email} - {self.role.name}"
  
  def is_valid(self):
    """この権限割り当てが現在有効かチェック"""
    now = timezone.now()
    if self.valid_from > now:
      return False
    if self.valid_until and self.valid_until < now:
      return False
    return True

""" ロールと権限の多対多関係"""
class RolePermission(models.Model):
  role = models.ForeignKey(
    Role,
    on_delete=models.CASCADE,
    related_name='role_permissions'
  )
  permission = models.ForeignKey(
    Permission,
    on_delete=models.CASCADE,
    related_name='permission_roles'
  )
  
  granted_by = models.ForeignKey(
      User,
      on_delete=models.SET_NULL,
      null=True,
      related_name='granted_permissions',
      verbose_name='付与者'
  )
  granted_at = models.DateTimeField('付与日時', auto_now_add=True)
  objects = RolePermissionManager()
  class Meta:
      db_table = 'role_permissions'
      verbose_name = 'Role Permission'
      verbose_name_plural = 'Role Permissions'
      unique_together = [['role', 'permission']]
  
  def __str__(self):
      return f"{self.role.name} - {self.permission.code}"
  