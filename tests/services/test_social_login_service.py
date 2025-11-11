import pytest
from django.core.exceptions import ValidationError
from core.services.social_login_service import SocialLoginService
from core.models import User
from tests.conftest import (
    OwnerFactory,
    CompanyFactory,
    TenantFactory,
    StaffFactory,
    StaffInvitationFactory,
    CustomerFactory
)


@pytest.mark.django_db
class TestExtractSocialData:
    """extract_social_dataメソッドのテスト"""
    
    def test_nc_109_extract_google_data(self, google_extra_data):
        """NC-109: Google extra_dataの抽出"""
        result = SocialLoginService.extract_social_data('google', google_extra_data)
        
        assert result['first_name'] == '太郎'
        assert result['last_name'] == '山田'
        assert result['email'] == 'test@example.com'
        assert result['email_verified'] is True
        assert result['picture'] == 'https://example.com/photo.jpg'
        assert result['language'] == 'ja'
    
    def test_nc_110_extract_apple_data_with_name(self, apple_extra_data):
        """NC-110: Apple extra_dataの抽出（初回、名前あり）"""
        result = SocialLoginService.extract_social_data('apple', apple_extra_data)
        
        assert result['first_name'] == '太郎'
        assert result['last_name'] == '山田'
        assert result['email'] == 'test@privaterelay.appleid.com'
        assert result['email_verified'] is True
        assert result['picture'] == ''
        assert result['language'] == 'ja'
    
    def test_ed_103_extract_apple_data_without_name(self, apple_extra_data_no_name):
        """ED-103: Appleで名前情報がない（2回目以降）"""
        result = SocialLoginService.extract_social_data('apple', apple_extra_data_no_name)
        
        assert result['first_name'] == ''
        assert result['last_name'] == ''
        assert result['email'] == 'test@privaterelay.appleid.com'
        assert result['email_verified'] is True
    
    def test_nc_111_extract_facebook_data(self, facebook_extra_data):
        """NC-111: Facebook extra_dataの抽出"""
        result = SocialLoginService.extract_social_data('facebook', facebook_extra_data)
        
        assert result['first_name'] == '太郎'
        assert result['last_name'] == '山田'
        assert result['email'] == 'test@example.com'
        assert result['email_verified'] is True
        assert result['picture'] == 'https://facebook.com/photo.jpg'
        assert result['language'] == 'ja'
    
    def test_ed_101_extract_with_empty_extra_data(self):
        """ED-101: extra_dataが空"""
        result = SocialLoginService.extract_social_data('google', {})
        
        assert result['first_name'] == ''
        assert result['last_name'] == ''
        assert result['email'] == ''
        assert result['email_verified'] is False
        assert result['picture'] == ''
        assert result['language'] == 'ja'
    
    def test_ed_102_extract_with_missing_fields(self):
        """ED-102: extra_dataに必須フィールドがない"""
        minimal_data = {'sub': '123'}
        result = SocialLoginService.extract_social_data('google', minimal_data)
        
        assert result['email'] == ''
        assert result['first_name'] == ''
    
    def test_ed_104_apple_email_verified_as_string(self):
        """ED-104: email_verifiedが文字列 'true'/'false'"""
        data = {
            'sub': '123',
            'email': 'test@example.com',
            'email_verified': 'true'
        }
        result = SocialLoginService.extract_social_data('apple', data)
        assert result['email_verified'] is True
        
        data['email_verified'] = 'false'
        result = SocialLoginService.extract_social_data('apple', data)
        assert result['email_verified'] is False
        
        data['email_verified'] = 'TRUE'
        result = SocialLoginService.extract_social_data('apple', data)
        assert result['email_verified'] is True
    
    def test_ed_105_facebook_picture_not_nested(self):
        """ED-105: Facebookのpictureが入れ子構造でない"""
        data = {
            'id': '123',
            'email': 'test@example.com',
            'first_name': '太郎',
            'last_name': '山田',
            'picture': 'not_a_dict',
            'locale': 'ja_JP'
        }
        result = SocialLoginService.extract_social_data('facebook', data)
        assert result['picture'] == ''
    
    def test_ed_106_locale_unexpected_format(self):
        """ED-106: localeが予期しない形式"""
        # Googleで地域コードなし
        data = {'locale': 'ja', 'email': 'test@example.com'}
        result = SocialLoginService.extract_social_data('google', data)
        assert result['language'] == 'ja'
        
        # Facebookでアンダースコアなし
        data = {'locale': 'ja', 'email': 'test@example.com'}
        result = SocialLoginService.extract_social_data('facebook', data)
        assert result['language'] == 'ja'
        
        # 空文字列
        data = {'locale': '', 'email': 'test@example.com'}
        result = SocialLoginService.extract_social_data('google', data)
        assert result['language'] == 'ja'


@pytest.mark.django_db
class TestGetOrCreateUser:
    """get_or_create_userメソッドのテスト"""
    
    def test_nc_101_create_new_user_with_google(self, mocker):
        """NC-101: Googleで新規ユーザー作成"""
        # mock_user = mocker.Mock()
        # mock_user.email = 'newuser@example.com'
        
        # social_dataは実際のオブジェクトを使う
        class SocialData:
            def __init__(self):
                self.email = 'newuser@example.com'
                self.first_name = '太郎'
                self.last_name = '山田'
                self.picture = 'https://example.com/pic.jpg'
        
        social_data = SocialData()
        
        user, created, message = SocialLoginService.get_or_create_user(
            validated_user_type='CUSTOMER',
            provider='google',
            uid='1234567890',
            social_data=social_data,
            form_data=None,
            invitation=None
        )
        
        assert created is True
        assert user.email == 'newuser@example.com'
        assert user.google_user_id == '1234567890'
        assert user.user_type == 'CUSTOMER'
        assert user.auth_provider == 'google'
        assert user.is_active is True
        assert user.is_email_verified is True
        assert not user.has_usable_password()
    
    def test_nc_104_existing_user_by_provider_id(self, customer_user, mocker):
        """NC-104: 既存ユーザーがソーシャルログイン（プロバイダーIDで発見）"""
        customer_user.google_user_id = '1234567890'
        customer_user.save()
        
        mock_user = mocker.Mock()
        mock_user.email = 'different@example.com'
        
        # 実際のオブジェクトを使う
        class SocialData:
            def __init__(self):
                self.email = 'different@example.com'
                self.picture = ''
        
        social_data = SocialData()
        
        user, created, message = SocialLoginService.get_or_create_user(
            validated_user_type='CUSTOMER',
            provider='google',
            uid='1234567890',
            social_data=social_data,
            form_data=None,
            invitation=None
        )
        
        assert created is False
        assert user.id == customer_user.id
        assert user.email == 'different@example.com'
        assert message == 'Googleアカウントでログインしました'
    
    def test_nc_105_existing_user_by_email(self, mocker):
        """NC-105: 既存ユーザーがソーシャルログイン（メールで発見）"""
        from tests.conftest import CustomerFactory
        
        existing_user = CustomerFactory(
            email='existing@example.com',
        )
        
        mock_user = mocker.Mock()
        mock_user.email = existing_user.email
        
        class SocialData:
            def __init__(self):
                self.email = 'existing@example.com'
                self.picture = 'https://example.com/new.jpg'
        
        social_data = SocialData()
        
        user, created, message = SocialLoginService.get_or_create_user(
            validated_user_type='CUSTOMER',
            provider='google',
            uid='9999999999',
            social_data=social_data,
            form_data=None,
            invitation=None
        )
        
        assert created is False
        assert user.id == existing_user.id
        assert user.google_user_id == '9999999999'
        assert user.auth_provider == 'google'
        assert user.email == 'existing@example.com'
        assert message == 'Googleアカウントを追加しましたしました'
    
    def test_nc_106_activate_staff_with_social(self, valid_invitation, mocker):
        """NC-106: スタッフのソーシャルアクティベート（招待あり）"""
        mock_user = mocker.Mock()
        mock_user.email = valid_invitation.user.email
        
        class SocialData:
            def __init__(self):
                self.email = valid_invitation.user.email
                self.first_name = '花子'
                self.last_name = '鈴木'
                self.picture = 'https://example.com/pic.jpg'
        
        social_data = SocialData()
        
        form_data = {
            'phone_number': '0987654321',
            'language': 'en',
            'address': '123 Test St',
            'suburb': 'Sydney',
            'state': 'NSW',
            'post_code': '2000'
        }
        
        user, created, message = SocialLoginService.get_or_create_user(
            validated_user_type='STAFF',
            provider='google',
            uid='1234567890',
            social_data=social_data,
            form_data=form_data,
            invitation=valid_invitation
        )
        
        assert created is True
        assert message == 'Googleでアカウントをアクティベートしました'
        assert user.id == valid_invitation.user.id
        assert user.is_active is True
        assert user.is_email_verified is True
        assert user.user_type == 'STAFF'
        assert user.google_user_id == '1234567890'
        assert user.auth_provider == 'google'
    
    def test_ec_101_staff_without_invitation(self, mocker):
        """EC-101: 招待なしでスタッフをソーシャル登録"""
        # この場合、validate_user_typeで既にエラーになるはず
        
        mock_user = mocker.Mock()
        mock_user.email = 'staff@example.com'
        
        social_data = mocker.Mock()
        social_data.email = 'staff@example.com'
        
        # validated_user_typeがSTAFFだが招待がない場合
        # 実際にはvalidate_user_typeでエラーになるが、
        # このメソッド内でもチェックが必要
        with pytest.raises(ValidationError):
            SocialLoginService.get_or_create_user(
                validated_user_type='STAFF',
                provider='google',
                uid='1234567890',
                social_data=social_data,
                form_data=None,
                invitation=None
            )
    
    def test_ec_102_invitation_without_user(self, mocker):
        """EC-102: 招待にユーザー情報がない"""
        mock_invitation = mocker.Mock()
        mock_invitation.user = None
        
        mock_user = mocker.Mock()
        mock_user.email = 'test@example.com'
        
        social_data = mocker.Mock()
        social_data.email = 'test@example.com'
        
        with pytest.raises(ValidationError) as exc_info:
            SocialLoginService.get_or_create_user(
                validated_user_type='STAFF',
                provider='google',
                uid='1234567890',
                social_data=social_data,
                form_data=None,
                invitation=mock_invitation
            )
        
        assert '招待にユーザー情報が含まれていません' in str(exc_info.value)
    
    def test_ec_103_activate_already_active_staff(self, active_staff_user, owner_user, tenant, mocker):
        """EC-103: 既にアクティブなユーザーをソーシャルアクティベート"""
        invitation = StaffInvitationFactory(
            invited_by=owner_user,
            tenant=tenant,
            user=active_staff_user
        )
        
        mock_user = mocker.Mock()
        mock_user.email = active_staff_user.email
        
        social_data = mocker.Mock()
        social_data.email = active_staff_user.email
        
        with pytest.raises(ValidationError) as exc_info:
            SocialLoginService.get_or_create_user(
                validated_user_type='STAFF',
                provider='google',
                uid='1234567890',
                social_data=social_data,
                form_data=None,
                invitation=invitation
            )
        
        assert 'このユーザーは既に登録済みです' in str(exc_info.value)


@pytest.mark.django_db
class TestPrepareUserDataFromForm:
    """prepare_user_data_from_formメソッドのテスト"""
    
    def test_prepare_with_full_form(self, mocker):
        """フォームデータの完全な準備"""
        mock_form = mocker.Mock()
        mock_form.cleaned_data = {
            'phone_number': '0123456789',
            'language': 'en',
            'address': '123 Test St',
            'suburb': 'Sydney',
            'state': 'NSW',
            'post_code': '2000'
        }
        
        result = SocialLoginService.prepare_user_data_from_form(mock_form)
        
        assert result['phone_number'] == '0123456789'
        assert result['language'] == 'en'
        assert result['profile_data']['address'] == '123 Test St'
        assert result['profile_data']['suburb'] == 'Sydney'
        assert result['profile_data']['state'] == 'NSW'
        assert result['profile_data']['post_code'] == '2000'
    
    def test_ed_301_prepare_with_none_form(self):
        """ED-301: formがNone"""
        result = SocialLoginService.prepare_user_data_from_form(None)
        
        assert result['phone_number'] is None
        assert result['language'] is None
        assert result['profile_data'] == {}
    
    def test_ed_302_prepare_without_cleaned_data(self, mocker):
        """ED-302: formにcleaned_dataがない"""
        mock_form = mocker.Mock(spec=[])  # cleaned_data属性なし
        
        result = SocialLoginService.prepare_user_data_from_form(mock_form)
        
        assert result['phone_number'] is None
        assert result['language'] is None
        assert result['profile_data'] == {}
    
    def test_prepare_with_partial_data(self, mocker):
        """部分的なフォームデータ"""
        mock_form = mocker.Mock()
        mock_form.cleaned_data = {
            'phone_number': '0123456789',
            'address': '123 Test St'
        }
        
        result = SocialLoginService.prepare_user_data_from_form(mock_form)
        
        assert result['phone_number'] == '0123456789'
        assert result['language'] is None
        assert 'address' in result['profile_data']
        assert 'suburb' not in result['profile_data']