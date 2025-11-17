from django.contrib.auth.backends import ModelBackend
from users.models import User

class CustomerAuthBackend(ModelBackend):
  def authenticate(self, request, username=None, password=None, **kwargs):
    if username is None or password is None:
      return None
    
    try:
      user = User.objects.get( email=username, user_group='CUSTOMER')
    except User.DoesNotExist:
      return None  
    
    if user.check_password(password) and self.user_can_authenticate(user):
      return user
    
    return None


class StaffOwnerAuthBackend(ModelBackend):
  def authenticate(self, request, username=None, password=None, **kwargs):
    if username is None or password is None:
      return None
    
    try:
      user = User.objects.get(email=username, user_group='STAFF_OWNER')
    except User.DoesNotExist:
      return None
    
    if user.check_password(password) and self.user_can_authenticate(user):
      return user
    
    return None