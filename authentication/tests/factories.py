import factory
from factory.django import DjangoModelFactory
from django.utils import timezone as django_timezone
from datetime import timedelta
import uuid
from users.models import User
from authentication.models import PendingUser
from django.contrib.auth.hashers import make_password
import secrets


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
  user_timezone = 'Asia/Tokyo'
  language = 'ja'
  
  @factory.post_generation
  def password(self, create, extracted):
    if not create:
      return
    
    if extracted:
      self.set_password(extracted)
    else:
      self.set_password('testpassword123')
  
  @factory.post_generation
  def groups(self, create, extracted):
    if not create:
      return
    
    if extracted:
      for group in extracted:
        self.groups.add(group)


class PendingUserFactory(DjangoModelFactory):
  class Meta:
    model = PendingUser
  
  email = factory.Faker('email')
  user_type = 'CUSTOMER'
  first_name = '太郎'
  last_name = '山田'
  country = 'JP'
  user_timezone = 'Asia/Tokyo'
  password_hash = factory.LazyFunction(
    lambda: make_password('testpassword123')
  )
  verification_token = factory.LazyFunction(
    lambda: secrets.token_urlsafe(32)
  )
  token_expires_at = factory.LazyFunction(
    lambda: django_timezone.now() + timedelta(hours=24)
  )
  user = None

  