import factory
from factory.django import DjangoModelFactory
from django.utils import timezone
from datetime import timedelta
import uuid
from core.models import (
  User, 
  StaffProfile, 
  StaffInvitation, 
  StaffRegistrationProgress,
  Tenant,
  TenantMembership,
  Company
)


class UserFactory(DjangoModelFactory):
  class Meta:
    model = User
  
  id = factory.LazyFunction(uuid.uuid4)
  email = factory.Sequence(lambda n: f'user{n}@example.com')
  user_type = 'CUSTOMER'
  first_name = '太郎'
  last_name = '山田'
  is_active = True
  is_email_verified = False
  auth_provider = 'email'
  country = 'JP'
  timezone = 'Asia/Tokyo'
  language = 'ja'
  
  @factory.post_generation
  def password(self, create, extracted, **kwargs):
    if not create:
      return
    if extracted:
      self.set_password(extracted)
    else:
      self.set_password('testpass123')


class CompanyFactory(DjangoModelFactory):
  class Meta:
    model = Company

  id = factory.LazyFunction(uuid.uuid4)
  name = factory.Sequence(lambda n: f'会社{n}')

class TenantFactory(DjangoModelFactory):
  class Meta:
    model = Tenant
    
  id = factory.LazyFunction(uuid.uuid4)
  name = factory.Sequence(lambda n: f'テナント{n}')
  company = factory.SubFactory(CompanyFactory)
  code = factory.Sequence(lambda n: f"tenant-{n}")



class StaffProfileFactory(DjangoModelFactory):
  class Meta:
    model = StaffProfile
  
  user = factory.SubFactory(UserFactory, user_type='STAFF')
  address = '東京都渋谷区'
  suburb = '渋谷'
  state = '東京都'
  post_code = '150-0001'


class StaffRegistrationProgressFactory(DjangoModelFactory):
  class Meta:
    model = StaffRegistrationProgress
  
  user = factory.SubFactory(UserFactory, user_type='STAFF')
  step = 'basic_info'


class StaffInvitationFactory(DjangoModelFactory):
  class Meta:
    model = StaffInvitation
  
  id = factory.LazyFunction(uuid.uuid4)
  token = factory.LazyFunction(lambda: uuid.uuid4().hex)
  invited_by = factory.SubFactory(UserFactory, user_type='OWNER')
  tenant = factory.SubFactory(TenantFactory)
  user = factory.SubFactory(
    UserFactory, 
    user_type='STAFF', 
    is_active=False,
    is_email_verified=False
  )
  email = factory.LazyAttribute(lambda obj: obj.user.email)
  first_name = '太郎'
  last_name = '山田'
  language = 'ja'
  country = 'JP'
  timezone = 'Asia/Tokyo'
  is_used = False
  expires_at = factory.LazyFunction(lambda: timezone.now() + timedelta(days=7))


class TenantMembershipFactory(DjangoModelFactory):
  class Meta:
    model = TenantMembership

  id = factory.LazyFunction(uuid.uuid4)
  tenant = factory.SubFactory(TenantFactory)
  user = factory.SubFactory(UserFactory, user_type='STAFF')
  is_active = True