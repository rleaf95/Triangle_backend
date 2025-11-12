from rest_framework import serializers
from core.models import User
from django.contrib.auth import authenticate

class ValidateInvitationSerializer(serializers.Serializer):
  """招待トークンの検証用"""
  token = serializers.CharField(required=True, max_length=255)


class SignupSerializer(serializers.Serializer):
  """サインアップ用"""
  session_token = serializers.CharField(required=False, allow_blank=True, max_length=64)

  user_type = serializers.ChoiceField(required=True ,choices=["STAFF", "OWNER", "CUSTOMER"])
  email = serializers.EmailField(required=True)
  password = serializers.CharField(write_only=True, min_length=8)
  first_name = serializers.CharField(required=False, max_length=150)
  last_name = serializers.CharField(required=False, max_length=150)
  phone_number = serializers.CharField(required=False, allow_blank=True, max_length=20)
  address = serializers.CharField(required=False, allow_blank=True, max_length=255)
  suburb = serializers.CharField(required=False, allow_blank=True, max_length=100)
  state = serializers.CharField(required=False, allow_blank=True, max_length=100)
  post_code = serializers.CharField(required=False, allow_blank=True, max_length=20)
  language = serializers.CharField(required=False, default='ja', max_length=10)
  country = serializers.CharField(required=False, default='AU', max_length=10)
  timezone = serializers.CharField(required=False, allow_blank=True, max_length=50)
  picture = serializers.URLField(required=False, allow_blank=True)


class EmailConfirmSerializer(serializers.Serializer):
  """メール確認用"""
  key = serializers.CharField(required=True, max_length=64)


class SocialLoginSerializer(serializers.Serializer):
  """ソーシャルログイン用Serializer"""
  provider = serializers.ChoiceField(choices=['google', 'line', 'facebook'])
  access_token = serializers.CharField(required=True)
  session_token = serializers.CharField(required=False, allow_blank=True)

  is_completing_signup = serializers.BooleanField(default=False)
  temp_token = serializers.CharField(required=False, allow_blank=True)
  address = serializers.CharField(required=False, allow_blank=True)
  suburb = serializers.CharField(required=False, allow_blank=True)
  state = serializers.EmailField(required=False, allow_blank=True)
  post_code = serializers.EmailField(required=False, allow_blank=True)
  phone_number = serializers.CharField(required=False, allow_blank=True, max_length=20)
  language = serializers.CharField(required=False, default='ja', max_length=10)