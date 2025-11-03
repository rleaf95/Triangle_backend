from core.models import User, OwnerProfile, StaffProfile
from django.core.exceptions import ObjectDoesNotExist

"""プロファイル管理サービス"""
class ProfileService:
  
  """オーナープロファイルを取得または作成"""
  @staticmethod
  def get_or_create_owner_profile(user, **defaults):
    if user.user_type != 'OWNER':
      raise ValueError('このユーザーはオーナーではありません')
    
    profile, created = OwnerProfile.objects.get_or_create(
      user=user,
      defaults=defaults
    )
    return profile, created
    
  """スタッフプロファイルを取得または作成"""
  @staticmethod
  def get_or_create_staff_profile(user, **defaults):
    if user.user_type != 'STAFF':
      raise ValueError('このユーザーはスタッフではありません')
    
    profile, created = StaffProfile.objects.get_or_create(
      user=user,
      defaults=defaults
    )
    return profile, created
    
  """オーナープロファイルを更新"""
  @staticmethod
  def update_owner_profile(user, **update_data):
    profile = ProfileService.get_or_create_owner_profile(user)
    
    allowed_fields = ['first_name', 'last_name', 'image',]
    
    for field, value in update_data.items():
      if field in allowed_fields:
        setattr(profile, field, value)
    
    profile.save()
    return profile
    
  @staticmethod
  def update_staff_profile(user, **update_data):
    """スタッフプロファイルを更新"""
    profile, _ = ProfileService.get_or_create_staff_profile(user)
      
    # 更新可能なフィールド
    allowed_fields = [
      'first_name', 'last_name', 'address', 'suburb',
      'state', 'post_code', 'phone_number',' unemployed_date','image'
    ]
      
    for field, value in update_data.items():
      if field in allowed_fields:
        setattr(profile, field, value)
    
    profile.save()
    return profile
    
  """プロファイルの完成度をチェック"""
  @staticmethod
  def get_profile_completion_status(user):
    if user.user_type == 'OWNER':
      try:
        profile = user.owner_profile
        missing_fields = []
        
        if not profile.first_name:
          missing_fields.append('first_name')
        if not profile.last_name:
          missing_fields.append('last_name')
        
        return {
          'is_complete': len(missing_fields) == 0,
          'missing_fields': missing_fields,
          'completion_rate': (2 - len(missing_fields)) / 2 * 100
        }
      except ObjectDoesNotExist:
        return {
          'is_complete': False,
          'missing_fields': ['first_name', 'last_name'],
          'completion_rate': 0
        }
      
    elif user.user_type == 'STAFF':
      try:
        profile = user.staff_profile
        required_fields = {
          'first_name': profile.first_name,
          'last_name': profile.last_name,
          'address': profile.address,
          'suburb': profile.suburb,
          'state': profile.state,
          'post_code': profile.post_code,
          'country': profile.country,
          'phone_number' : profile.phone_number,
        }
        
        missing_fields = [k for k, v in required_fields.items() if not v]
        
        return {
          'is_complete': len(missing_fields) == 0,
          'missing_fields': missing_fields,
          'completion_rate': (len(required_fields) - len(missing_fields)) / len(required_fields) * 100
        }
      except ObjectDoesNotExist:
        return {
          'is_complete': False,
          'missing_fields': ['first_name', 'last_name', 'address', 'suburb', 'state', 'post_code', 'country', 'phone_number'],
          'completion_rate': 0
        }
  
    return {'is_complete': True, 'missing_fields': [], 'completion_rate': 100}
  
  """複数ユーザーのプロファイル情報を効率的に取得"""
  @staticmethod
  def get_users_with_profiles(user_queryset):
    users = user_queryset.select_related(
      'owner_profile',
      'staff_profile'
    )
    if user.profile_image:
      image = user.profile_image
    elif user.profile_image_url:
      image = user.profile_image_url
    else:
      image = None

    result = []
    for user in users:
      user_data = {
        'id': user.id,
        'email': user.email,
        'user_type': user.user_type,
        'image': image,
        'profile': None,
      }
      
      try:
        if user.user_type == 'OWNER':
          profile = user.owner_profile
          user_data['profile'] = {
            'first_name': profile.first_name,
            'last_name': profile.last_name,
          }
        elif user.user_type == 'STAFF':
          profile = user.staff_profile
          user_data['profile'] = {
            'first_name': profile.first_name,
            'last_name': profile.last_name,
            'address' : profile.address,
            'suburb' : profile.suburb,
            'state' : profile.state,
            'post_code' : profile.post_code,
            'phone_number' : profile.phone_number,
            'hire_date' : profile.hire_date,
            'unemployed_date' : profile.unemployed_date,
          }
      except ObjectDoesNotExist:
        pass
      
      result.append(user_data)
    
    return result