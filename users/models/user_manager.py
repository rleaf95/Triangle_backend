
from django.contrib.auth.models import BaseUserManager
from .user_querysets import UserQuerySet
from django.core.exceptions import ValidationError


class UserManager(BaseUserManager):
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
  
  def email_exists_in_group(self, email, user_type):
    if user_type == 'CUSTOMER':
      return self.by_email(email).customers().first()
    
    elif user_type in ['STAFF', 'OWNER']:
      return self.by_email(email).staff_or_owner().first()
    
    return None
  
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
  

  # === ユーザーを作成メソッド ===
  
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

