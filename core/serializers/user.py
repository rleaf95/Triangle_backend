# apps/accounts/serializers/user.py

from rest_framework import serializers
from apps.accounts.models import User, Profile


class ProfileSerializer(serializers.ModelSerializer):
  """プロフィールSerializer"""
  
  class Meta:
    model = Profile
    fields = ['address', 'suburb', 'state', 'post_code',]

class UserSerializer(serializers.ModelSerializer):
  """ユーザーSerializer"""
  
  profile = ProfileSerializer(read_only=True)
  class Meta:
    model = User
    fields = ['id', 'email', 'first_name', 'last_name', 'phone_number', 'user_type', 'profile', ]
    read_only_fields = ['id', 'user_type']
