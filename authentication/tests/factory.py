import factory
from factory.django import DjangoModelFactory
from django.utils import timezone
from datetime import timedelta
import uuid
from users.models import User, StaffProfile, StaffRegistrationProgress
from invitation.models import StaffInvitation
from organizations.models import Tenant,  Company
from permissions.models import TenantMembership

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