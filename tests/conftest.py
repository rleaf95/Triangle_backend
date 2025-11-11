import pytest
from django.utils import timezone
from datetime import timedelta
import factory
from factory.django import DjangoModelFactory
from factory import Faker, SubFactory, LazyAttribute, post_generation
from core.models import User, StaffInvitation, Tenant, Company
import secrets

# ===== Factories =====

class UserFactory(DjangoModelFactory):
    """ユーザーファクトリ"""
    class Meta:
        model = User
        django_get_or_create = ('email',)
    
    email = Faker('email')
    first_name = Faker('first_name')
    last_name = Faker('last_name')
    user_type = 'CUSTOMER'
    language = 'ja'
    country = 'AU'
    timezone = 'Australia/Sydney'
    auth_provider = 'email'
    is_active = True
    is_email_verified = False
    phone_number = Faker('phone_number')
    
    @post_generation
    def password(obj, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            obj.set_password(extracted)
        else:
            obj.set_password('testpass123')


class OwnerFactory(UserFactory):
    """オーナーファクトリ"""
    user_type = 'OWNER'
    is_email_verified = True


class CustomerFactory(UserFactory):
    """カスタマーファクトリ"""
    user_type = 'CUSTOMER'


class StaffFactory(UserFactory):
    """スタッフファクトリ（未アクティブ）"""
    user_type = 'STAFF'
    is_active = False
    is_email_verified = False


class CompanyFactory(DjangoModelFactory):
    """会社ファクトリ"""
    class Meta:
        model = Company
    
    name = Faker('company')
    abn = Faker('bothify', text='## ### ### ###')


class TenantFactory(DjangoModelFactory):
    """テナントファクトリ"""
    class Meta:
        model = Tenant
    
    company = SubFactory(CompanyFactory)  # ← Companyが必要
    name = Faker('company')
    code = LazyAttribute(lambda x: f"TEST{secrets.token_hex(3).upper()}")
    address = Faker('address')
    suburb = Faker('city')
    state = 'NSW'
    post_code = Faker('postcode')
    country = 'AU'
    phone_number = Faker('phone_number')
    email = Faker('email')
    is_active = True


class StaffInvitationFactory(DjangoModelFactory):
    """スタッフ招待ファクトリ"""
    class Meta:
        model = StaffInvitation
    
    token = LazyAttribute(lambda x: secrets.token_urlsafe(32))
    invited_by = SubFactory(OwnerFactory)
    tenant = SubFactory(TenantFactory)
    user = SubFactory(StaffFactory)
    email = LazyAttribute(lambda obj: obj.user.email)
    first_name = Faker('first_name')
    last_name = Faker('last_name')
    language = 'ja'
    country = 'AU'
    timezone = 'Australia/Sydney'
    is_used = False
    expires_at = LazyAttribute(lambda x: timezone.now() + timedelta(days=7))


# ===== Fixtures =====

@pytest.fixture
def owner_user(db):
    """オーナーユーザー"""
    return OwnerFactory()


@pytest.fixture
def customer_user(db):
    """カスタマーユーザー"""
    return CustomerFactory()


@pytest.fixture
def inactive_staff_user(db):
    """未アクティブスタッフユーザー"""
    return StaffFactory()


@pytest.fixture
def active_staff_user(db):
    """アクティブスタッフユーザー"""
    return StaffFactory(is_active=True, is_email_verified=True)


@pytest.fixture
def company(db):
    """会社"""
    return CompanyFactory()


@pytest.fixture
def tenant(db, company):
    """テナント"""
    return TenantFactory(company=company)


@pytest.fixture
def valid_invitation(db):
    """有効な招待"""
    owner = OwnerFactory()
    company = CompanyFactory()
    tenant = TenantFactory(company=company)
    staff = StaffFactory()
    
    return StaffInvitationFactory(
        invited_by=owner,
        tenant=tenant,
        user=staff,
        email=staff.email,
        is_used=False,
        expires_at=timezone.now() + timedelta(days=7)
    )


@pytest.fixture
def expired_invitation(db):
    """期限切れ招待"""
    owner = OwnerFactory()
    company = CompanyFactory()
    tenant = TenantFactory(company=company)
    staff = StaffFactory()
    
    return StaffInvitationFactory(
        invited_by=owner,
        tenant=tenant,
        user=staff,
        is_used=False,
        expires_at=timezone.now() - timedelta(days=1)
    )


@pytest.fixture
def used_invitation(db):
    """使用済み招待"""
    owner = OwnerFactory()
    company = CompanyFactory()
    tenant = TenantFactory(company=company)
    staff = StaffFactory(is_active=True, is_email_verified=True)
    
    return StaffInvitationFactory(
        invited_by=owner,
        tenant=tenant,
        user=staff,
        is_used=True,
        used_at=timezone.now() - timedelta(days=1)
    )


@pytest.fixture
def google_extra_data():
    """Google extra_data"""
    return {
        'sub': '1234567890',
        'email': 'test@example.com',
        'given_name': '太郎',
        'family_name': '山田',
        'picture': 'https://example.com/photo.jpg',
        'locale': 'ja',
        'email_verified': True
    }


@pytest.fixture
def apple_extra_data():
    """Apple extra_data（初回）"""
    return {
        'sub': 'abc123.xyz456',
        'email': 'test@privaterelay.appleid.com',
        'email_verified': 'true',
        'is_private_email': True,
        'name': {
            'firstName': '太郎',
            'lastName': '山田'
        }
    }


@pytest.fixture
def apple_extra_data_no_name():
    """Apple extra_data（2回目以降、名前なし）"""
    return {
        'sub': 'abc123.xyz456',
        'email': 'test@privaterelay.appleid.com',
        'email_verified': True,
        'is_private_email': True
    }


@pytest.fixture
def facebook_extra_data():
    """Facebook extra_data"""
    return {
        'id': '9876543210',
        'email': 'test@example.com',
        'first_name': '太郎',
        'last_name': '山田',
        'picture': {
            'data': {
                'height': 50,
                'is_silhouette': False,
                'url': 'https://facebook.com/photo.jpg',
                'width': 50
            }
        },
        'locale': 'ja_JP'
    }


@pytest.fixture
def mock_sociallogin(mocker):
    """モックSocialLogin"""
    mock = mocker.Mock()
    mock.account.provider = 'google'
    mock.account.uid = '1234567890'
    mock.account.extra_data = {
        'sub': '1234567890',
        'email': 'test@example.com',
        'given_name': '太郎',
        'family_name': '山田',
        'picture': 'https://example.com/photo.jpg',
        'locale': 'ja',
        'email_verified': True
    }
    mock.user.email = 'test@example.com'
    mock.user.first_name = '太郎'
    mock.user.last_name = '山田'
    return mock