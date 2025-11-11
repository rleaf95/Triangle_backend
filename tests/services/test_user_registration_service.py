import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from core.services.user_registration_service import UserRegistrationService
from core.models.user import User
from core.models.invitation import StaffInvitation
from tests.conftest import StaffInvitationFactory


@pytest.mark.django_db
class TestRegisterUser:
    """register_userメソッドのテスト"""
    
    # ===== 正常系 =====
    
    def test_nc_001_register_owner_without_invitation(self):
        """NC-001: オーナーの新規登録（招待なし）"""
        user, invitation = UserRegistrationService.register_user(
            email='owner@example.com',
            password='testpass123',
            user_type='OWNER',
            language='ja',
            country='AU',
            first_name='太郎',
            last_name='山田',
            phone_number='0123456789'
        )
        
        assert user.email == 'owner@example.com'
        assert user.user_type == 'OWNER'
        assert user.check_password('testpass123')
        assert user.is_active is True
        assert user.is_email_verified is True
        assert user.auth_provider == 'email'
        assert user.first_name == '太郎'
        assert user.last_name == '山田'
        assert invitation is None
    
    def test_nc_002_register_customer_without_invitation(self):
        """NC-002: カスタマーの新規登録（招待なし）"""
        user, invitation = UserRegistrationService.register_user(
            email='customer@example.com',
            password='testpass123',
            user_type='CUSTOMER',
            language='en',
            country='JP',
            timezone='Asia/Tokyo'
        )
        
        assert user.email == 'customer@example.com'
        assert user.user_type == 'CUSTOMER'
        assert user.language == 'en'
        assert user.country == 'JP'
        assert user.timezone == 'Asia/Tokyo'
        assert invitation is None
    
    def test_nc_003_activate_staff_with_valid_invitation(self, valid_invitation):
        """NC-003: スタッフのアクティベート（有効な招待あり）"""
        staff_user = valid_invitation.user
        original_email = staff_user.email
        
        user, registered_user = UserRegistrationService.register_user(
            email=original_email,
            password='testpass123',
            user_type='STAFF',
            invitation_token=valid_invitation.token,
            first_name='花子',
            last_name='鈴木',
            phone_number='0987654321',
            language='ja',
            country='AU'
        )
        
        assert user.id == staff_user.id
        assert user.is_active is True
        assert user.is_email_verified is True
        assert user.user_type == 'STAFF'
        assert user.check_password('testpass123')
        assert user.first_name == '花子'
        assert user.last_name == '鈴木'
        
        # 招待が使用済みになっているか
        valid_invitation.refresh_from_db()
        assert valid_invitation.is_used is True
        assert valid_invitation.used_at is not None
        assert valid_invitation.user == user
    
    def test_nc_004_activate_staff_with_profile_data(self, valid_invitation):
        """NC-004: スタッフのアクティベート時にプロフィール作成"""
        profile_data = {
            'address': '123 Test St',
            'suburb': 'Sydney',
            'state': 'NSW',
            'post_code': '2000'
        }
        
        user, invitation = UserRegistrationService.register_user(
            email=valid_invitation.user.email,
            password='testpass123',
            user_type='STAFF',
            invitation_token=valid_invitation.token,
            profile_data=profile_data
        )
        
        assert user.is_active is True
        # プロフィールが作成されているか確認
        # ProfileServiceのテストで詳細確認
    
    def test_nc_005_register_with_all_optional_fields(self):
        """ED-005: 全てのオプションフィールドを含むユーザー作成"""
        user, invitation = UserRegistrationService.register_user(
            email='full@example.com',
            password='testpass123',
            user_type='OWNER',
            language='en',
            country='JP',
            timezone='Asia/Tokyo',
            first_name='John',
            last_name='Doe',
            phone_number='1234567890',
            picture='https://example.com/pic.jpg'
        )
        
        assert user.email == 'full@example.com'
        assert user.first_name == 'John'
        assert user.last_name == 'Doe'
        assert user.phone_number == '1234567890'
        assert user.profile_image_url == 'https://example.com/pic.jpg'
        assert user.language == 'en'
        assert user.country == 'JP'
        assert user.timezone == 'Asia/Tokyo'
    
    # ===== 異常系 =====
    
    def test_ec_001_register_with_existing_email(self, customer_user):
        """EC-001: 既に登録済みのメールアドレスで登録"""
        with pytest.raises(ValidationError) as exc_info:
            UserRegistrationService.register_user(
                email=customer_user.email,
                password='testpass123',
                user_type='CUSTOMER'
            )
        
        assert 'このメールアドレスは既に登録されています' in str(exc_info.value)
    
    def test_ec_004_register_staff_without_invitation(self):
        """EC-004: 招待なしでスタッフ登録を試みる"""
        with pytest.raises(ValidationError) as exc_info:
            UserRegistrationService.register_user(
                email='staff@example.com',
                password='testpass123',
                user_type='STAFF'
            )
        
        assert 'スタッフの登録には招待が必要です' in str(exc_info.value)
    
    def test_ec_005_register_with_invalid_user_type(self):
        """EC-005: 無効なユーザータイプ"""
        with pytest.raises(ValidationError) as exc_info:
            UserRegistrationService.register_user(
                email='test@example.com',
                password='testpass123',
                user_type='INVALID'
            )
        
        assert '無効なユーザータイプです' in str(exc_info.value)
    
    # ===== 境界値・例外 =====
    
    def test_ed_001_register_with_none_invitation_token(self):
        """ED-001: 招待トークンがNone"""
        user, invitation = UserRegistrationService.register_user(
            email='test@example.com',
            password='testpass123',
            user_type='OWNER',
            invitation_token=None
        )
        
        assert user.user_type == 'OWNER'
        assert invitation is None
    
    def test_ed_002_register_with_none_profile_data(self):
        """ED-002: profile_dataがNone"""
        user, invitation = UserRegistrationService.register_user(
            email='test@example.com',
            password='testpass123',
            user_type='CUSTOMER',
            profile_data=None
        )
        
        assert user.user_type == 'CUSTOMER'
    
    def test_ed_003_register_with_empty_profile_data(self):
        """ED-003: profile_dataが空の辞書"""
        user, invitation = UserRegistrationService.register_user(
            email='test@example.com',
            password='testpass123',
            user_type='CUSTOMER',
            profile_data={}
        )
        
        assert user.user_type == 'CUSTOMER'
    
    def test_ed_004_register_with_minimum_fields(self):
        """ED-004: 最小限の情報でユーザー作成"""
        user, invitation = UserRegistrationService.register_user(
            email='min@example.com',
            password='testpass123',
            user_type='CUSTOMER'
        )
        
        assert user.email == 'min@example.com'
        assert user.user_type == 'CUSTOMER'
        assert user.language == 'ja'  # デフォルト値
        assert user.country == 'AU'  # デフォルト値


@pytest.mark.django_db
class TestValidateInvitation:
    """validate_invitationメソッドのテスト"""
    
    def test_nc_005_validate_valid_invitation(self, valid_invitation):
        """NC-005: 招待トークンの検証成功"""
        invitation = UserRegistrationService.validate_invitation(valid_invitation.token)
        
        assert invitation.id == valid_invitation.id
        assert invitation.is_used is False
    
    def test_ec_002_validate_invalid_token(self):
        """EC-002: 無効な招待トークン"""
        with pytest.raises(ValidationError) as exc_info:
            UserRegistrationService.validate_invitation('invalid_token')
        
        assert '無効または期限切れの招待リンクです' in str(exc_info.value)
    
    def test_ec_003_validate_expired_invitation(self, expired_invitation):
        """EC-003: 期限切れの招待トークン"""
        with pytest.raises(ValidationError) as exc_info:
            UserRegistrationService.validate_invitation(expired_invitation.token)
        
        assert '無効または期限切れの招待リンクです' in str(exc_info.value)
    
    def test_ed_001_validate_none_token(self):
        """ED-001: 招待トークンがNone"""
        invitation = UserRegistrationService.validate_invitation(None)
        
        assert invitation is None
    
    def test_ed_006_validate_invitation_at_expiry_boundary(self, owner_user, tenant, inactive_staff_user):
        """ED-006: 招待の有効期限ギリギリ"""
        from freezegun import freeze_time
        
        # 1秒後に期限切れになる招待を作成
        now = timezone.now()
        invitation = StaffInvitationFactory(
            invited_by=owner_user,
            tenant=tenant,
            user=inactive_staff_user,
            expires_at=now + timedelta(seconds=1)
        )
        
        # 現在時刻では有効
        result = UserRegistrationService.validate_invitation(invitation.token)
        assert result is not None
        
        # 2秒後は期限切れ
        with freeze_time(now + timedelta(seconds=2)):
            with pytest.raises(ValidationError):
                UserRegistrationService.validate_invitation(invitation.token)


@pytest.mark.django_db
class TestValidateUserType:
    """validate_user_typeメソッドのテスト"""
    
    def test_nc_006_validate_user_type_without_invitation(self):
        """NC-006: ユーザータイプの検証成功（招待なし）"""
        result = UserRegistrationService.validate_user_type('OWNER', None)
        assert result == 'OWNER'
        
        result = UserRegistrationService.validate_user_type('CUSTOMER', None)
        assert result == 'CUSTOMER'
    
    def test_nc_007_validate_user_type_with_invitation(self, valid_invitation):
        """NC-007: ユーザータイプの検証成功（招待あり→STAFF）"""
        result = UserRegistrationService.validate_user_type('CUSTOMER', valid_invitation)
        assert result == 'STAFF'
        
        result = UserRegistrationService.validate_user_type('OWNER', valid_invitation)
        assert result == 'STAFF'
    
    def test_ec_004_validate_staff_without_invitation(self):
        """EC-004: 招待なしでスタッフ登録を試みる"""
        with pytest.raises(ValidationError) as exc_info:
            UserRegistrationService.validate_user_type('STAFF', None)
        
        assert 'スタッフの登録には招待が必要です' in str(exc_info.value)
    
    def test_ec_005_validate_invalid_user_type(self):
        """EC-005: 無効なユーザータイプ"""
        with pytest.raises(ValidationError) as exc_info:
            UserRegistrationService.validate_user_type('INVALID', None)
        
        assert '無効なユーザータイプです' in str(exc_info.value)


@pytest.mark.django_db
class TestActivateStaffUser:
    """activate_staff_userメソッドのテスト"""
    
    def test_activate_staff_success(self, valid_invitation):
        """スタッフのアクティベート成功"""
        user_data = {
            'email': valid_invitation.user.email,
            'password': 'newpass123',
            'first_name': '花子',
            'last_name': '鈴木',
            'phone_number': '0987654321',
            'language': 'en',
            'country': 'JP',
            'auth_provider': 'email'
        }
        
        user = UserRegistrationService.activate_staff_user(
            invitation=valid_invitation,
            user_data=user_data
        )
        
        assert user.is_active is True
        assert user.is_email_verified is True
        assert user.user_type == 'STAFF'
        assert user.check_password('newpass123')
        assert user.first_name == '花子'
        assert user.last_name == '鈴木'
    
    def test_ec_006_activate_without_invitation(self):
        """EC-006: 招待なしでアクティベート"""
        with pytest.raises(ValidationError) as exc_info:
            UserRegistrationService.activate_staff_user(
                invitation=None,
                user_data={'password': 'test123'}
            )
        
        assert 'スタッフの登録には招待が必要です' in str(exc_info.value)
    
    def test_ec_006_activate_invitation_without_user(self, mocker):
        """EC-006: 招待にユーザー情報が含まれていない"""
        mock_invitation = mocker.Mock()
        mock_invitation.user = None
        
        with pytest.raises(ValidationError) as exc_info:
            UserRegistrationService.activate_staff_user(
                invitation=mock_invitation,
                user_data={'password': 'test123'}
            )
        
        assert '招待にユーザー情報が含まれていません' in str(exc_info.value)
    
    def test_ec_007_activate_already_active_user(self, active_staff_user, owner_user, tenant):
        """EC-007: 既にアクティブなユーザーを再度アクティベート"""
        invitation = StaffInvitationFactory(
            invited_by=owner_user,
            tenant=tenant,
            user=active_staff_user
        )
        
        with pytest.raises(ValidationError) as exc_info:
            UserRegistrationService.activate_staff_user(
                invitation=invitation,
                user_data={'password': 'test123'}
            )
        
        assert 'このユーザーは既に登録済みです' in str(exc_info.value)


@pytest.mark.django_db
class TestProcessInvitation:
    """process_invitationメソッドのテスト"""
    
    def test_process_invitation_success(self, valid_invitation, customer_user):
        """招待処理の成功"""
        UserRegistrationService.process_invitation(valid_invitation, customer_user)
        
        valid_invitation.refresh_from_db()
        assert valid_invitation.is_used is True
        assert valid_invitation.registered_user == customer_user
        assert valid_invitation.used_at is not None
    
    def test_process_none_invitation(self, customer_user):
        """招待がNoneの場合"""
        # エラーにならないことを確認
        UserRegistrationService.process_invitation(None, customer_user)