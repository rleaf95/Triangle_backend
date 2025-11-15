
from rest_framework import serializers
from users.models import User, StaffProfile, StaffRegistrationProgress, CustomerRegistrationProgress


class ProfileSerializer(serializers.ModelSerializer):
  class Meta:
    model = StaffProfile
    fields = ['address', 'suburb', 'state', 'post_code',]

class StaffProgressSerializer(serializers.ModelSerializer):
  class Meta:
    model = StaffRegistrationProgress
    fields = ['step']

class CustomerProgressSerializer(serializers.ModelSerializer):
  class Meta:
    model = CustomerRegistrationProgress
    fields = ['step']


class UserSerializer(serializers.ModelSerializer):
  profile = ProfileSerializer(read_only=True)
  progress = serializers.SerializerMethodField()

  class Meta:
    model = User
    fields = [
      'id', 'email', 'first_name', 'last_name',
      'phone_number', 'user_type', 'profile', 'progress'
    ]
    read_only_fields = ['id', 'user_type']

  def get_progress(self, obj):
    if obj.user_type == 'STAFF':
      if hasattr(obj, 'staff_progress') and obj.staff_progress is not None:
        progress = obj.staff_progress
      else:
        try:
          progress = obj.staff_progress
        except StaffRegistrationProgress.DoesNotExist:
          return None
      return StaffProgressSerializer(progress).data
    
    elif obj.user_type == 'CUSTOMER':
      if hasattr(obj, 'customer_progress') and obj.customer_progress is not None:
        progress = obj.customer_progress
      else:
        try:
          progress = obj.customer_progress
        except CustomerRegistrationProgress.DoesNotExist:
          return None
      return CustomerProgressSerializer(progress).data
    
    return None
  
  def get_profile(self, obj):
    if obj.user_type == 'STAFF':
      if hasattr(obj, '_staff_profile'):
        profile = obj._staff_profile
      else:
        try:
          profile = obj.staff_profile
        except StaffProfile.DoesNotExist:
          return None
      return ProfileSerializer(profile).data
    return None

  def __init__(self, *args, **kwargs):
    fields = kwargs.pop('fields', None)
    super().__init__(*args, **kwargs)
    if fields is not None:
      allowed = set(fields)
      existing = set(self.fields.keys())
      for field_name in list(existing - allowed):
        self.fields.pop(field_name)