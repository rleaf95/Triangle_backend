# # from django.core.exceptions import ValidationError
# # from django.core.cache import cache
# # from rest_framework_simplejwt.tokens import RefreshToken

# # from invitation.models import StaffInvitation
# # from users.models import User

# class RegistrationUtilsService:
  
#   @classmethod
#   def handle_profile_creation(cls, user, profile_data=None):
#     """プロファイル作成・更新の共通処理"""
#     if profile_data:
#       if user.user_type == 'STAFF':
#         ProfileService.get_or_create_staff_profile(user, profile_data)
#       else:
#         pass
    

  
#   @classmethod
#   def create_user_relationships(cls, user):
#     """
#     ユーザーと会社・テナントの関連を作成（オーナー用）
#     """
#     if user.user_type == 'OWNER':
#       cls._create_owner_relationships(user)
#     else:
#       pass
  
#   @classmethod
#   def _create_owner_relationships(cls, user):
#     """
#     オーナーの関連を作成
#     新規登録の場合は後で会社作成時に紐付けるため、ここでは何もしない
#     """
#     # TODO: 必要に応じて実装
#     pass
  
#   @classmethod
#   def _create_customer_relationships(cls, user):
#     """カスタマーの関連を作成"""
#     # TODO: 必要に応じて実装
#     pass
  
#   @classmethod
#   def process_invitation(cls, invitation, user):
#     """招待を処理（使用済みにする）"""
#     if invitation:
#       invitation.is_used = True
#       invitation.registered_user = user
#       invitation.used_at = timezone.now()
#       invitation.save()