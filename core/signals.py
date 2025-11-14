from django.db.models.signals import post_save
from django.dispatch import receiver
from core.models import User, StaffProfile, StaffRegistrationProgress, CustomerRegistrationProgress

@receiver(post_save, sender=User)
def create_user_related_objects(sender, instance, created, **kwargs):
  if created:
    if instance.user_type == 'CUSTOMER':
      if not instance.first_name or not instance.last_name or not instance.phone_number:
        step = 'detail'
      else:
        step = 'done'
      CustomerRegistrationProgress.objects.create(user=instance, step=step)
  
    elif instance.user_type == 'STAFF':
      StaffProfile.objects.create(user=instance)
      StaffRegistrationProgress.objects.create(
          user=instance,
          step='basic_info'
      )