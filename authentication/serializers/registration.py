from rest_framework import serializers
from django.contrib.auth import authenticate
from ..utils import DisposableEmailChecker
from django.utils.translation import gettext as _
from django.contrib.auth.password_validation import validate_password as django_validate_password
from django.core.exceptions import ValidationError as DjangoValidationError




class OwnerSignupSerializer(serializers.Serializer):
  """サインアップ用"""
  user_type = serializers.ChoiceField(required=True ,choices=["OWNER"])
  email = serializers.EmailField(required=True)
  password = serializers.CharField(write_only=True, min_length=8)
  confirm_password = serializers.CharField(write_only=True, min_length=8)
  country = serializers.CharField(required=False, default='AU', max_length=10)
  user_timezone = serializers.CharField(required=False, allow_blank=True, max_length=50)
  first_name =  serializers.CharField(required=True, max_length=50)
  last_name = serializers.CharField(required=True, max_length=50)

  def validate_email(self, value):
    """メールアドレスのバリデーション"""
    email = value.lower().strip()
    
    if DisposableEmailChecker.is_disposable(email):
      raise serializers.ValidationError(_('使い捨てメールアドレスは使用できません。'))
    return email
  
  def validate_password(self, value):
    try:
        django_validate_password(value)
    except DjangoValidationError as e:
        raise serializers.ValidationError(list(e.messages))
    return value
    
  def validate(self, data):
    if data['password'] != data['confirm_password']:
        raise serializers.ValidationError({
            'confirm_password': _('パスワードが一致しません。')
        })
    data.pop('confirm_password')
    
    return data
  
class CustomerSignupSerializer(serializers.Serializer):
  """サインアップ用"""
  user_type = serializers.ChoiceField(required=True ,choices=["OWNER"])
  email = serializers.EmailField(required=True)
  password = serializers.CharField(write_only=True, min_length=8)
  country = serializers.CharField(required=False, default='AU', max_length=10)
  user_timezone = serializers.CharField(required=False, allow_blank=True, max_length=50)
  first_name =  serializers.CharField(required=True, max_length=50)
  last_name = serializers.CharField(required=True, max_length=50)
  
  def validate_email(self, value):
    """メールアドレスのバリデーション"""
    email = value.lower().strip()
    
    if DisposableEmailChecker.is_disposable(email):
      raise serializers.ValidationError(_('使い捨てメールアドレスは使用できません。'))
    return email

class EmailConfirmSerializer(serializers.Serializer):
  """メール確認用"""
  key = serializers.CharField(required=True, max_length=64)

class EmailChangeSerializer(serializers.Serializer):
  """メールアドレス変更用"""
  old_email = serializers.EmailField(required=True)
  new_email = serializers.EmailField(required=True)

  def validate_new_email(self, value):
    """メールアドレスのバリデーション"""
    new_email = value.lower().strip()
    
    if DisposableEmailChecker.is_disposable(new_email):
      raise serializers.ValidationError(_('使い捨てメールアドレスは使用できません。'))
    return new_email

class SocialLoginSerializer(serializers.Serializer):
  """ソーシャルログイン用Serializer"""
  provider = serializers.ChoiceField(choices=['google', 'line', 'facebook'])
  access_token = serializers.CharField(required=True)
  user_type = serializers.ChoiceField(required=True ,choices=["STAFF", "OWNER", "CUSTOMER"])
  id_token = serializers.CharField(required=False)
