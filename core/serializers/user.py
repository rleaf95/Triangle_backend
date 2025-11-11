from rest_framework import serializers
from core.models import User
from django.contrib.auth import authenticate

class UserSerializer(serializers.ModelSerializer):
  """認証レスポンス用"""
  profile_image_display = serializers.SerializerMethodField()

  #!後で必要ないデータは消す
  class Meta:
    model = User
    fields = [
      'id', 'email', 'user_type', 'is_email_verified',
      'language', 'timezone', 'auth_provider', 'date_joined',
      'profile_image_url', 'profile_image_display',
    ]
    read_only_fields = ['id', 'date_joined', 'auth_provider']
  
  def get_profile_image_display(self, obj):
    """プロフィール画像のURLを返す"""
    if obj.profile_image:
      request = self.context.get('request')
      if request:
        return request.build_absolute_uri(obj.profile_image.url)
      return obj.profile_image.url
    
    if obj.profile_image_url:
      return obj.profile_image_url
    
    return None


class UserDetailSerializer(serializers.ModelSerializer):
  """詳細なユーザー情報（プロファイル含む）"""
  owner_profile = serializers.SerializerMethodField()
  staff_profile = serializers.SerializerMethodField()
  profile_image_display = serializers.SerializerMethodField()
  
  class Meta:
    model = User
    fields = [
      'id', 'email', 'user_type', 'is_email_verified',
      'language', 'timezone', 'auth_provider', 'date_joined',
      'country', 'profile_image_url', 'profile_image_display',
      'owner_profile', 'staff_profile'
    ]
    read_only_fields = ['id', 'date_joined', 'auth_provider', 'updated_at']
  
  def get_profile_image_display(self, obj):
    """プロフィール画像のURLを返す"""
    if obj.profile_image:
      request = self.context.get('request')
      if request:
        return request.build_absolute_uri(obj.profile_image.url)
      return obj.profile_image.url
    
    if obj.profile_image_url:
      return obj.profile_image_url
    
    return None
  
  def get_owner_profile(self, obj):
    if obj.user_type == 'OWNER' and hasattr(obj, 'owner_profile'):
      from .profile import OwnerProfileSerializer
      return OwnerProfileSerializer(obj.owner_profile).data
    return None
  
  def get_staff_profile(self, obj):
    if obj.user_type == 'STAFF' and hasattr(obj, 'staff_profile'):
      from .profile import StaffProfileSerializer
      return StaffProfileSerializer(obj.staff_profile).data
    return None


class UserRegistrationSerializer(serializers.Serializer):
    """メール登録用"""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    user_type = serializers.ChoiceField(choices=['OWNER', 'CUSTOMER'])
    language = serializers.ChoiceField(
      choices=['ja', 'en'],
      default='en',
      required=False
    )
    invitation_token = serializers.CharField(required=False, allow_blank=True)
    
    first_name = serializers.CharField(max_length=50)
    last_name = serializers.CharField(max_length=50)
    
    def validate_email(self, value):
      if User.objects.filter(email=value).exists():
        raise serializers.ValidationError('このメールアドレスは既に使用されています')
      return value
    
    def validate(self, data):
      if data.get('password') != data.get('password_confirm'):
        raise serializers.ValidationError({'password_confirm': 'パスワードが一致しません'})
      return data
    
    def validate_user_type(self, value):
      invitation_token = self.initial_data.get('invitation_token')
      if value == 'STAFF' and not invitation_token:
        raise serializers.ValidationError('スタッフの登録には招待が必要です')
      return value
    
    def create(self, validated_data):
      """ユーザー作成"""
      from ..services.user_registration_service import UserRegistrationService
      from core.services.profile_service import ProfileService
      
      validated_data.pop('password_confirm')
      
      profile_data = {}
      if validated_data.get('first_name'):
        profile_data['first_name'] = validated_data.pop('first_name')
      if validated_data.get('last_name'):
        profile_data['last_name'] = validated_data.pop('last_name')
      
      # ユーザー作成
      user, invitation = UserRegistrationService.register_user(
        email=validated_data['email'],
        password=validated_data['password'],
        user_type=validated_data['user_type'],
        language=validated_data.get('language', 'ja'),
        auth_provider='email',
        invitation_token=validated_data.get('invitation_token'),
        profile_data=profile_data if profile_data else None
      )
      
      return user


class EmailLoginSerializer(serializers.Serializer):
    """メールログイン用"""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        """認証チェック"""
        email = data.get('email')
        password = data.get('password')
        
        if email and password:
            # ユーザー存在チェック
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                raise serializers.ValidationError('メールアドレスまたはパスワードが正しくありません')
            
            # パスワードチェック
            if not user.check_password(password):
                raise serializers.ValidationError('メールアドレスまたはパスワードが正しくありません')
            
            # アクティブチェック
            if not user.is_active:
                raise serializers.ValidationError('このアカウントは無効化されています')
            
            data['user'] = user
        else:
            raise serializers.ValidationError('メールアドレスとパスワードは必須です')
        
        return data