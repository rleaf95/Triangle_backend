from rest_framework import serializers
from django.contrib.auth import authenticate




class OwnerSignupSerializer(serializers.Serializer):
  """サインアップ用"""
  session_token = serializers.CharField(required=False, allow_blank=True, max_length=64)
  user_type = serializers.ChoiceField(required=True ,choices=["OWNER"])
  email = serializers.EmailField(required=True)
  password = serializers.CharField(write_only=True, min_length=8)
  country = serializers.CharField(required=False, default='AU', max_length=10)
  timezone = serializers.CharField(required=False, allow_blank=True, max_length=50)

class CustomerSignupSerializer(serializers.Serializer):
  """サインアップ用"""
  session_token = serializers.CharField(required=False, allow_blank=True, max_length=64)
  user_type = serializers.ChoiceField(required=True ,choices=["OWNER"])
  email = serializers.EmailField(required=True)
  password = serializers.CharField(write_only=True, min_length=8)
  country = serializers.CharField(required=False, default='AU', max_length=10)
  timezone = serializers.CharField(required=False, allow_blank=True, max_length=50)

class EmailConfirmSerializer(serializers.Serializer):
  """メール確認用"""
  key = serializers.CharField(required=True, max_length=64)


class SocialLoginSerializer(serializers.Serializer):
  """ソーシャルログイン用Serializer"""
  provider = serializers.ChoiceField(choices=['google', 'line', 'facebook'])
  access_token = serializers.CharField(required=True)
  user_type = serializers.ChoiceField(required=True ,choices=["STAFF", "OWNER", "CUSTOMER"])
  id_token = serializers.CharField(required=False)
