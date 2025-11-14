import pytest
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import transaction, IntegrityError
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, MagicMock
from core.models import User, StaffProfile, StaffInvitation, StaffRegistrationProgress
from core.services.user_registration_service import UserRegistrationService
from core.services.social_login_service import SocialLoginService
from ...factories import UserFactory, StaffInvitationFactory, StaffProfileFactory


@pytest.mark.django_db
class TestTransactionRollback:
  """トランザクションロールバックのテスト"""
  
  def test_8_1_1_successful_transaction(self):
    """8.1.1: 正常なトランザクション完了"""
    invitation = StaffInvitationFactory()
    session_token = 'test_session_token'
    
    cache_key = f'invitation_session:{session_token}'
    cache.set(cache_key, {
      'invitation_id': str(invitation.id),
      'invitation_token': invitation.token,
      'email': invitation.email,
    }, timeout=900)
    
    data = {
      'email': invitation.email,
      'password': 'testpass123',
    }
    
    user, refresh, _ = UserRegistrationService.register_user(
      session_token=session_token,
      user_type='STAFF',
      data=data,
    )
    
    # 全てコミットされている
    assert User.objects.filter(id=user.id).exists()
    assert StaffProfile.objects.filter(user=user).exists()
    assert StaffRegistrationProgress.objects.filter(user=user).exists()
    
    invitation.refresh_from_db()
    assert invitation.is_used is True
  
  
  def test_8_1_3_invitation_save_failure(self):
    """8.1.3: 招待使用済み処理失敗"""
    invitation = StaffInvitationFactory()
    session_token = 'test_session_token'
    
    cache_key = f'invitation_session:{session_token}'
    cache.set(cache_key, {
      'invitation_id': str(invitation.id),
      'invitation_token': invitation.token,
      'email': invitation.email,
    }, timeout=900)
    
    data = {
      'email': invitation.email,
      'password': 'testpass123',
    }
    
    # invitation.save をモックしてエラーを発生させる
    with patch.object(StaffInvitation, 'save') as mock_save:
      mock_save.side_effect = Exception("Invitation save failed")
      
      with pytest.raises(Exception, match="Invitation save failed"):
        UserRegistrationService.register_user(
          session_token=session_token,
          user_type='STAFF',
          data=data,
        )
      
      # ロールバックされているか確認
      invitation.refresh_from_db()
      assert invitation.is_used is False
  
  def test_8_1_4_progress_update_failure(self):
    """8.1.4: Progress更新失敗"""
    invitation = StaffInvitationFactory()
    session_token = 'test_session_token'
    
    cache_key = f'invitation_session:{session_token}'
    cache.set(cache_key, {
      'invitation_id': str(invitation.id),
      'invitation_token': invitation.token,
      'email': invitation.email,
    }, timeout=900)
    
    data = {
      'email': invitation.email,
      'password': 'testpass123',
    }
    
    with patch.object(StaffRegistrationProgress, 'save') as mock_save:
      mock_save.side_effect = Exception("Progress save failed")
      
      with pytest.raises(Exception, match="Progress save failed"):
        UserRegistrationService.register_user(
          session_token=session_token,
          user_type='STAFF',
          data=data,
        )


@pytest.mark.django_db
class TestRedisCache:
  """Redis/Cacheのテスト"""
  
  def test_8_2_1_session_saved_in_redis(self):
    """8.2.1: session保存の確認"""
    invitation = StaffInvitationFactory()
    session_token = 'test_session_token'
    
    cache_key = f'invitation_session:{session_token}'
    cache.set(cache_key, {
      'invitation_id': str(invitation.id),
      'invitation_token': invitation.token,
      'email': invitation.email,
    }, timeout=900)
    
    # 15分間保存されている
    session_data = cache.get(cache_key)
    assert session_data is not None
    assert session_data['invitation_id'] == str(invitation.id)
  
  def test_8_2_2_session_deleted_after_activation(self):
    """8.2.2: アクティベート成功時のsession削除"""
    invitation = StaffInvitationFactory()
    session_token = 'test_session_token'
    
    cache_key = f'invitation_session:{session_token}'
    cache.set(cache_key, {
      'invitation_id': str(invitation.id),
      'invitation_token': invitation.token,
      'email': invitation.email,
    }, timeout=900)
    
    data = {
      'email': invitation.email,
      'password': 'testpass123',
    }
    
    UserRegistrationService.register_user(
      session_token=session_token,
      user_type='STAFF',
      data=data,
    )
    
    # Redisから削除されている
    session_data = cache.get(cache_key)
    assert session_data is None
  
  def test_8_2_3_session_timeout(self):
    """8.2.3: session_tokenのタイムアウト"""
    invitation = StaffInvitationFactory()
    session_token = 'test_session_token'
    
    # Redisに保存しない（タイムアウト想定）
    
    data = {
      'email': invitation.email,
      'password': 'testpass123',
    }
    
    with pytest.raises(ValidationError, match='セッションが無効または期限切れです'):
      UserRegistrationService.register_user(
        session_token=session_token,
        user_type='STAFF',
        data=data,
      )
  
  def test_8_2_4_session_deleted_on_error(self):
    """8.2.4: エラー時のsession削除"""
    # 存在しない招待
    session_token = 'test_session_token'
    
    cache_key = f'invitation_session:{session_token}'
    cache.set(cache_key, {
      'invitation_id': 'nonexistent_id',
      'invitation_token': 'nonexistent_token',
      'email': 'test@example.com',
    }, timeout=900)
    
    data = {
      'email': 'test@example.com',
      'password': 'testpass123',
    }
    
    with pytest.raises(ValidationError, match='有効なUUIDではありません'):
      UserRegistrationService.register_user(
        session_token=session_token,
        user_type='STAFF',
        data=data,
      )
    
    session_data = cache.get(cache_key)
    assert session_data is None
  
  def test_8_2_5_redis_connection_error(self):
    """8.2.5: Redis接続エラー"""
    with patch('django.core.cache.cache.get') as mock_get:
      mock_get.side_effect = Exception("Redis connection error")
      
      data = {
        'email': 'test@example.com',
        'password': 'testpass123',
      }
      
      with pytest.raises(Exception, match="Redis connection error"):
        UserRegistrationService.register_user(
          session_token='test_session',
          user_type='STAFF',
          data=data,
        )


@pytest.mark.django_db
class TestConcurrentAccess:
  """並行処理のテスト"""
  
  def test_8_3_1_simultaneous_activation(self):
    """8.3.1: 同時アクティベート"""
    email = 'staff@example.com'
    invitation = StaffInvitationFactory(email=email)
    
    session_token = 'test_session_token'
    cache_key = f'invitation_session:{session_token}'
    cache.set(cache_key, {
      'invitation_id': str(invitation.id),
      'invitation_token': invitation.token,
      'email': invitation.email,
    }, timeout=900)
    
    data = {
      'email': email,
      'password': 'testpass123',
    }
    
    user1, _, _ = UserRegistrationService.register_user(
      session_token=session_token,
      user_type='STAFF',
      data=data,
    )
    
    cache.set(cache_key, {
      'invitation_id': str(invitation.id),
      'invitation_token': invitation.token,
      'email': invitation.email,
    }, timeout=900)
    
    with pytest.raises(ValidationError, match='招待が見つかりません'):
      UserRegistrationService.register_user(
        session_token=session_token,
        user_type='STAFF',
        data=data,
      )
  
  def test_8_3_2_simultaneous_signup(self):
    """8.3.2: 同時サインアップ"""
    email = 'customer@example.com'
    
    data = {
      'email': email,
      'password': 'testpass123',
    }
    
    # 1つ目成功
    user1, _, _ = UserRegistrationService.register_user(
      session_token=None,
      user_type='CUSTOMER',
      data=data,
    )
    
    # 2つ目は失敗（メールアドレス重複）
    with pytest.raises(Exception):
      UserRegistrationService.register_user(
        session_token=None,
        user_type='CUSTOMER',
        data=data,
      )
  
  def test_8_3_3_simultaneous_social_login(self, mock_google_api):
    """8.3.3: 同時ソーシャルログイン"""
    # 既存ユーザー
    existing_user = UserFactory(
      email='test@example.com',
      google_user_id='123456789'
    )
    
    # 1つ目成功
    user1, _, _ = SocialLoginService.get_or_create_user(
      user_type='CUSTOMER',
      access_token='valid_google_token',
      provider='google',
      session_token=None,
      id_token=None
    )
    
    # 2つ目も成功（既存ユーザーログイン）
    user2, _, _ = SocialLoginService.get_or_create_user(
      user_type='CUSTOMER',
      access_token='valid_google_token',
      provider='google',
      session_token=None,
      id_token=None
    )
    
    assert user1.id == existing_user.id
    assert user2.id == existing_user.id


@pytest.mark.django_db
class TestDataIntegrity:
  """データ整合性のテスト"""
  
  def test_8_4_1_invitation_without_user(self):
    """8.4.1: 招待なしユーザーのアクティベート"""
    # userが削除された招待
    invitation = StaffInvitationFactory()
    user_id = invitation.user.id
    invitation.user.delete()
    
    session_token = 'test_session_token'
    cache_key = f'invitation_session:{session_token}'
    cache.set(cache_key, {
      'invitation_id': str(invitation.id),
      'invitation_token': invitation.token,
      'email': invitation.email,
    }, timeout=900)
    
    data = {
      'email': invitation.email,
      'password': 'testpass123',
    }
    
    with pytest.raises(Exception):
      UserRegistrationService.register_user(
        session_token=session_token,
        user_type='STAFF',
        data=data,
      )
  
  def test_8_4_2_user_without_progress(self):
    """8.4.2: プログレスなしユーザー"""
    invitation = StaffInvitationFactory()
    # プログレスを削除
    StaffRegistrationProgress.objects.filter(user=invitation.user).delete()
    
    session_token = 'test_session_token'
    cache_key = f'invitation_session:{session_token}'
    cache.set(cache_key, {
      'invitation_id': str(invitation.id),
      'invitation_token': invitation.token,
      'email': invitation.email,
    }, timeout=900)
    
    data = {
      'email': invitation.email,
      'password': 'testpass123',
    }
    
    with pytest.raises(Exception):
      UserRegistrationService.register_user(
        session_token=session_token,
        user_type='STAFF',
        data=data,
      )
  
  def test_8_4_3_invitation_without_tenant(self):
    """8.4.3: Tenantなし招待"""
    invitation = StaffInvitationFactory()
    tenant_id = invitation.tenant.id
    invitation.tenant.delete()
    
    session_token = 'test_session_token'
    cache_key = f'invitation_session:{session_token}'
    cache.set(cache_key, {
      'invitation_id': str(invitation.id),
      'invitation_token': invitation.token,
      'email': invitation.email,
    }, timeout=900)
    
    data = {
      'email': invitation.email,
      'password': 'testpass123',
    }
    
    with pytest.raises(Exception):
      UserRegistrationService.register_user(
        session_token=session_token,
        user_type='STAFF',
        data=data,
      )


@pytest.mark.django_db
class TestProviderSpecificEdgeCases:
  """プロバイダー特有のエッジケース"""
  
  def test_8_5_1_google_verified_email_false(self):
    """8.5.1: verified_email=False"""
    with patch('core.services.social_login_service.requests.get') as mock_get:
      response = MagicMock()
      response.raise_for_status = MagicMock()
      response.json.return_value = {
        'id': '123456789',
        'email': 'test@example.com',
        'given_name': '太郎',
        'family_name': '山田',
        'verified_email': False
      }
      mock_get.return_value = response
      
      user, _, _ = SocialLoginService.get_or_create_user(
        user_type='CUSTOMER',
        access_token='valid_google_token',
        provider='google',
        session_token=None,
        id_token=None
      )
      
      # verified_email=False の場合
      assert user.is_email_verified is False
  
  def test_8_5_2_google_no_given_family_name(self, mock_google_api_no_name):
    """8.5.2: given_name/family_nameなし"""
    user, _, _ = SocialLoginService.get_or_create_user(
      user_type='CUSTOMER',
      access_token='valid_google_token',
      provider='google',
      session_token=None,
      id_token=None
    )
    
    assert user.first_name == ''
    assert user.last_name == ''
  
  def test_8_5_3_google_no_picture(self, mock_google_api_no_picture):
    """8.5.3: pictureなし"""
    user, _, _ = SocialLoginService.get_or_create_user(
      user_type='CUSTOMER',
      access_token='valid_google_token',
      provider='google',
      session_token=None,
      id_token=None
    )
    
    assert user.profile_image_url == ''
  
  
  def test_8_5_5_line_sub_and_user_id_mismatch(self):
    """8.5.5: id_token.subとuserIdの不一致"""
    with patch('core.services.social_login_service.requests.get') as mock_get, \
        patch('core.services.social_login_service.jwt.decode') as mock_jwt:
      
      def get_side_effect(url, *args, **kwargs):
        response = MagicMock()
        response.raise_for_status = MagicMock()
        
        if 'line.me/v2/profile' in url:
          response.json.return_value = {
            'userId': 'different_user_id',
            'displayName': '山田太郎',
          }
        return response
      
      mock_get.side_effect = get_side_effect
      mock_jwt.return_value = {
        'sub': 'U1234567890abcdef',
        'email': 'test@example.com'
      }
      
      user, _, _ = SocialLoginService.get_or_create_user(
        user_type='CUSTOMER',
        access_token='valid_line_token',
        provider='line',
        session_token=None,
        id_token='valid_id_token'
      )
      
      # id_token.sub を優先
      assert user.line_user_id == 'U1234567890abcdef'
  
  def test_8_5_6_line_no_picture_url(self, mock_line_api_no_picture):
    """8.5.6: pictureUrlなし"""
    user, _, _ = SocialLoginService.get_or_create_user(
      user_type='CUSTOMER',
      access_token='valid_line_token',
      provider='line',
      session_token=None,
      id_token='valid_id_token'
    )
    
    assert user.profile_image_url == None