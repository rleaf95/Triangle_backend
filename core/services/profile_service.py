from core.models import User, StaffProfile
from django.core.exceptions import ObjectDoesNotExist

"""プロファイル管理サービス"""
class ProfileService:
  
  """オーナープロファイルを取得または作成"""
  # @staticmethod
  # def get_or_create_owner_profile(user, **defaults):
  #   if user.user_type != 'OWNER':
  #     raise ValueError('このユーザーはオーナーではありません')
    
  #   profile, created = OwnerProfile.objects.get_or_create(
  #     user=user,
  #     defaults=defaults
  #   )
  #   return profile, created
    
  """スタッフプロファイルを取得または作成"""
  @staticmethod
  def get_or_create_staff_profile(user, profile_data):
    profile = user.staff_profile  # キャッシュから取得
    if profile_data:
      for key, value in profile_data.items():
        if hasattr(profile, key):
          setattr(profile, key, value)
      profile.save()
    
    progress = user.staff_progress

    if profile_data and any(not value for value in profile_data.values()):
      progress.step = 'profile'
    progress.step = 'done'
    progress.save()
    
    return profile
    
  """オーナープロファイルを更新"""
  # @staticmethod
  # def update_owner_profile(user, **update_data):
  #   profile = ProfileService.get_or_create_owner_profile(user)
    
  #   allowed_fields = ['first_name', 'last_name',]
    
  #   for field, value in update_data.items():
  #     if field in allowed_fields:
  #       setattr(profile, field, value)
    
  #   profile.save()
  #   return profile
    
  @staticmethod
  def update_staff_profile(user, **update_data):
    """スタッフプロファイルを更新"""
    profile, _ = ProfileService.get_or_create_staff_profile(user)
      
    # 更新可能なフィールド
    allowed_fields = [
      'address', 'suburb', 'state', 'post_code',' unemployed_date',
    ]
      
    for field, value in update_data.items():
      if field in allowed_fields:
        setattr(profile, field, value)
    
    profile.save()
    return profile
    