from django.db import models
from django.utils import timezone
from users.models import User
from django.db import transaction

class PendingUser(models.Model):

  COUNTRY_CHOICES = (
    ('AU', 'Australia'),
    ('JP', 'Japan'),
  )
  USER_TYPE_CHOICES = (
    ('OWNER', 'オーナー'),
    ('CUSTOMER', '顧客'),
  )

  email = models.EmailField(unique=True)
  password_hash = models.CharField(max_length=255)
  user_type = models.CharField(choices=USER_TYPE_CHOICES, max_length=20)
  country = models.CharField(max_length=2, choices=COUNTRY_CHOICES, blank=True, null=True )
  timezone = models.CharField('タイムゾーン', max_length=50, blank=True, null=True)

  #For link Sicial Account
  user = models.OneToOneField(User, blank=True, null=True, on_delete=models.CASCADE, related_name='pending_user', )

  verification_token = models.CharField(max_length=255, unique=True)
  token_expires_at = models.DateTimeField()
  created_at = models.DateTimeField(auto_now_add=True)
  
  class Meta:
    db_table = 'users_pending_user'
    constraints = [ 
      models.UniqueConstraint( 
        fields=['email', 'user_type'],
        name='unique_email_user_type'
      ),
    ]
    indexes = [
      models.Index(fields=['token_expires_at'], name='idx_pending_token_expires'),
      models.Index(fields=['email', 'user_type'], name='idx_email_pending_user_type'),
    ]
  
  def is_token_valid(self):
    return timezone.now() < self.token_expires_at
  
  @transaction.atomic
  def create_user(self):
    user = User.objects.create(
      email=self.email,
      password=self.password_hash,
      user_type=self.user_type,
      is_email_verified=True,
      is_active=True,
      auth_provider='email',
      country=self.country,
      timezone=self.timezone
    )
    self.delete()
    return user
  
  @transaction. atomic
  def link_social_account(self):
    user = self.user
    user.password=self.password_hash,
    user.auth_provider='email',
    update_fields = ['password', 'auth_provider']
    if user.is_email_verified != self.is_email_verified or user.is_active != self.is_active:
      user.is_email_verified=True,
      user.is_active=True,
      update_fields.append('is_email_verified', 'is_active')
    if user.country != self.country:
      user.country = self.country
      update_fields.append('country')
    if user.timezone != self.timezone:
      user.timezone = self.timezone
      update_fields.append('timezone')
    
    user.save(update_fields=update_fields)
    return user
    
    