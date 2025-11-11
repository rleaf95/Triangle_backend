import pytest
from django.core.exceptions import ValidationError
from core.adapters.allauth_adapters import (
    CustomAccountAdapter,
    CustomSocialAccountAdapter
)


@pytest.mark.django_db
class TestCustomAccountAdapter:
    """CustomAccountAdapterのテスト"""
    
    def test_nc_201_is_open_for_signup_without_invitation(self, rf):
        """NC-201: 招待なしで新規登録許可"""
        request = rf.get('/')
        request.session = {'user_type': 'OWNER'}
        
        adapter = CustomAccountAdapter()
        assert adapter.is_open_for_signup(request) is True
    
    def test_nc_202_is_open_for_signup_with_valid_invitation(self, rf, valid_invitation):
        """NC-202: 有効な招待で新規登録許可"""
        request = rf.get('/')
        request.session = {
            'staff_invitation_token': valid_invitation.token,
            'user_type': 'STAFF'
        }
        
        adapter = CustomAccountAdapter()
        assert adapter.is_open_for_signup(request) is True
    
    def test_ec_201_is_open_for_signup_with_invalid_invitation(self, rf):
        """EC-201: 無効な招待トークンで登録拒否"""
        request = rf.get('/')
        request.session = {
            'staff_invitation_token': 'invalid_token',
            'user_type': 'STAFF'
        }
        
        adapter = CustomAccountAdapter()
        assert adapter.is_open_for_signup(request) is False
    
    def test_nc_203_save_owner_user(self, rf, mocker):
        """NC-203: オーナーの保存"""
        request = rf.post('/')
        request.session = {'user_type': 'OWNER'}
        
        mock_user = mocker.Mock()
        mock_user.email = 'owner@example.com'
        mock_user.password = 'hashed_password'
        
        mock_form = mocker.Mock()
        mock_form.cleaned_data = {
            'email': 'owner@example.com',
            'first_name': '太郎',
            'last_name': '山田',
            'phone_number': '0123456789',
            'user_type': 'OWNER',
            'language': 'ja',
            'country': 'AU'
        }
        
        adapter = CustomAccountAdapter()
        user = adapter.save_user(request, mock_user, mock_form)
        
        assert user.user_type == 'OWNER'
        assert user.email == 'owner@example.com'
        assert 'user_type' not in request.session
    
    def test_nc_205_save_staff_user_with_invitation(self, rf, valid_invitation, mocker):
        """NC-205: スタッフのアクティベート"""
        request = rf.post('/')
        request.session = {
            'staff_invitation_token': valid_invitation.token,
            'user_type': 'STAFF'
        }
        
        mock_user = mocker.Mock()
        mock_user.email = valid_invitation.user.email
        mock_user.password = 'hashed_password'
        
        mock_form = mocker.Mock()
        mock_form.cleaned_data = {
            'email': valid_invitation.user.email,
            'first_name': '花子',
            'last_name': '鈴木',
            'phone_number': '0987654321',
            'language': 'ja',
            'country': 'AU',
            'address': '123 Test St',
            'suburb': 'Sydney',
            'state': 'NSW',
            'post_code': '2000'
        }
        
        adapter = CustomAccountAdapter()
        user = adapter.save_user(request, mock_user, mock_form)
        
        assert user.id == valid_invitation.user.id
        assert user.is_active is True
        assert user.user_type == 'STAFF'
        assert 'staff_invitation_token' not in request.session
    
    def test_ed_201_save_without_invitation_token_in_session(self, rf, mocker):
        """ED-201: 招待トークンがセッションにない"""
        request = rf.post('/')
        request.session = {
            'user_type': 'CUSTOMER'
        }
        
        mock_user = mocker.Mock()
        mock_user.email = 'customer@example.com'
        
        mock_form = mocker.Mock()
        mock_form.cleaned_data = {
            'email': 'customer@example.com',
            'user_type': 'CUSTOMER'
        }
        
        adapter = CustomAccountAdapter()
        user = adapter.save_user(request, mock_user, mock_form)
        
        assert user.user_type == 'CUSTOMER'
    
    def test_ed_202_save_without_user_type_in_session(self, rf, mocker):
        """ED-202: user_typeがセッションにない（デフォルト値）"""
        request = rf.post('/')
        request.session = {}
        
        mock_user = mocker.Mock()
        mock_user.email = 'test@example.com'
        
        mock_form = mocker.Mock()
        mock_form.cleaned_data = {
            'email': 'test@example.com'
        }
        
        adapter = CustomAccountAdapter()
        user = adapter.save_user(request, mock_user, mock_form)
        
        # デフォルトはCUSTOMER
        assert user.user_type == 'CUSTOMER'


@pytest.mark.django_db
class TestCustomSocialAccountAdapter:
    """CustomSocialAccountAdapterのテスト"""
    
    def test_nc_301_is_auto_signup_without_invitation(self, rf):
        """NC-301: 招待なしで自動サインアップ許可"""
        request = rf.get('/')
        request.session = {}
        
        adapter = CustomSocialAccountAdapter()
        assert adapter.is_auto_signup_allowed(request) is True
    
    def test_nc_302_is_auto_signup_with_invitation(self, rf, valid_invitation):
        """NC-302: 招待ありで自動サインアップ拒否（フォーム表示）"""
        request = rf.get('/')
        request.session = {'staff_invitation_token': valid_invitation.token}
        
        adapter = CustomSocialAccountAdapter()
        assert adapter.is_auto_signup_allowed(request) is False
    
    def test_nc_303_save_social_user(self, rf, mock_sociallogin, mocker):
        """NC-303: ソーシャルログインでユーザー保存"""
        request = rf.post('/')
        request.session = {'user_type': 'CUSTOMER'}
        
        adapter = CustomSocialAccountAdapter()
        user, created, message = adapter.save_user(request, mock_sociallogin, form=None)
        
        assert created is True
        assert user.email == 'test@example.com'
        assert user.google_user_id == '1234567890'
        assert 'user_type' not in request.session
        assert message == f'Googleでアカウントを作成しました'