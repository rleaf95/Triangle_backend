"""pytest全体の設定とフィクスチャ"""
import pytest
from rest_framework.test import APIClient
from faker import Faker
import fakeredis
from django.conf import settings

# Fakerの日本語設定
fake = Faker('ja_JP')


# ========================================
# 基本的なフィクスチャ
# ========================================

@pytest.fixture
def api_client():
  """APIクライアント"""
  return APIClient()


@pytest.fixture
def fake_redis():
  """テスト用のfake Redis"""
  redis_client = fakeredis.FakeStrictRedis(decode_responses=True)
  # テスト前にクリア
  redis_client.flushdb()
  return redis_client


@pytest.fixture
def authenticated_client(api_client, owner_user):
  """認証済みAPIクライアント"""
  api_client.force_authenticate(user=owner_user)
  return api_client



# ========================================
# 環境設定用フィクスチャ
# ========================================

@pytest.fixture(autouse=True)
def setup_test_environment(settings):
    """テスト環境の自動セットアップ"""
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """全テストでDBアクセスを有効化（必要に応じて）"""
    pass


# ========================================
# モック用フィクスチャ
# ========================================

@pytest.fixture(autouse=True)
def mock_redis_for_all_tests(mocker, fake_redis):
  """すべてのテストで自動的にRedisをモック"""
  mocker.patch(
    'common.utils.redis_client.get_redis_client',
    return_value=fake_redis
  )
  mocker.patch(
    'common.utils.rate_limiter.get_redis_client',
    return_value=fake_redis
  )
  return fake_redis



# @pytest.fixture
# def mock_email_send(mocker):
#   """メール送信をモック"""
#   return mocker.patch(
#     'apps.auth.services.AuthService._send_verification_email',
#     return_value=True
#   )