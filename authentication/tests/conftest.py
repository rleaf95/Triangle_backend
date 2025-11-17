import pytest
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, MagicMock
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from django.test.utils import CaptureQueriesContext
from django.db import connection
import requests
from django.test import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.storage.fallback import FallbackStorage


@pytest.fixture(autouse=True)
def clear_cache():
  """各テスト前後でRedisキャッシュをクリア"""
  cache.clear()
  yield
  cache.clear()


@pytest.fixture
def api_client():
  """APIクライアント"""
  return APIClient()


@pytest.fixture
def authenticated_client(api_client, user_factory):
  """認証済みAPIクライアント"""
  user = user_factory(user_type='CUSTOMER', is_active=True)
  refresh = RefreshToken.for_user(user)
  api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
  return api_client, user

@pytest.fixture
def mock_request():
  """django-allauth用のモックリクエスト"""
  factory = RequestFactory()
  request = factory.post('/')
  
  middleware = SessionMiddleware(lambda x: None)
  middleware.process_request(request)
  request.session.save()
  
  setattr(request, '_messages', FallbackStorage(request))
  
  return request


@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
  """Siteオブジェクトを作成"""
  with django_db_blocker.unblock():
    from django.contrib.sites.models import Site
    Site.objects.get_or_create(
      id=1,
      defaults={'domain': 'testserver', 'name': 'testserver'}
    )

@pytest.fixture
def mock_google_api():
  """Google API モック"""
  with patch('authentication.services.social_login_service.requests.get') as mock_get:
    def side_effect(url, *args, **kwargs):
      response = MagicMock()
      response.raise_for_status = MagicMock()
      
      if 'googleapis.com' in url:
        response.json.return_value = {
          'id': '123456789',
          'email': 'test@example.com',
          'given_name': '太郎',
          'family_name': '山田',
          'name': '山田太郎',
          'picture': 'https://example.com/photo.jpg',
          'verified_email': True
        }
      return response
    
    mock_get.side_effect = side_effect
    yield mock_get


@pytest.fixture
def mock_google_api_no_name():
  """Google API モック（名前なし）"""
  with patch('authentication.services.social_login_service.requests.get') as mock_get:
    def side_effect(url, *args, **kwargs):
      response = MagicMock()
      response.raise_for_status = MagicMock()
      
      if 'googleapis.com' in url:
        response.json.return_value = {
          'id': '123456789',
          'email': 'test@example.com',
          'verified_email': True
        }
      return response
    
    mock_get.side_effect = side_effect
    yield mock_get


@pytest.fixture
def mock_google_api_no_picture():
  """Google API モック（画像なし）"""
  with patch('authentication.services.social_login_service.requests.get') as mock_get:
    def side_effect(url, *args, **kwargs):
      response = MagicMock()
      response.raise_for_status = MagicMock()
      
      if 'googleapis.com' in url:
        response.json.return_value = {
          'id': '123456789',
          'email': 'test@example.com',
          'given_name': '太郎',
          'family_name': '山田',
          'verified_email': True
        }
      return response
    
    mock_get.side_effect = side_effect
    yield mock_get


@pytest.fixture
def mock_google_api_no_email():
  """Google API モック（メールなし）"""
  with patch('authentication.services.social_login_service.requests.get') as mock_get:
    def side_effect(url, *args, **kwargs):
      response = MagicMock()
      response.raise_for_status = MagicMock()
      
      if 'googleapis.com' in url:
        response.json.return_value = {
          'id': '123456789',
          'verified_email': True
        }
      return response
    
    mock_get.side_effect = side_effect
    yield mock_get


@pytest.fixture
def mock_google_api_error_401():
  """Google APIエラー 401 モック"""
  with patch('authentication.services.social_login_service.requests.get') as mock_get:
    response = MagicMock()
    response.status_code = 401
    response.reason = 'Unauthorized'
    
    http_error = requests.exceptions.HTTPError("401 Client Error: Unauthorized")
    http_error.response = response
    response.raise_for_status.side_effect = http_error
    
    mock_get.return_value = response
    yield mock_get

@pytest.fixture
def mock_google_api_error_403():
  """Google APIエラー 403 モック"""
  with patch('authentication.services.social_login_service.requests.get') as mock_get:
    response = MagicMock()
    response.status_code = 403
    response.reason = 'Forbidden'
    
    http_error = requests.exceptions.HTTPError("403 Client Error: Forbidden")
    http_error.response = response
    response.raise_for_status.side_effect = http_error
    
    mock_get.return_value = response
    yield mock_get


@pytest.fixture
def mock_google_api_error_500():
  """Google APIエラー 500 モック"""
  with patch('authentication.services.social_login_service.requests.get') as mock_get:
    response = MagicMock()
    response.status_code = 500
    response.reason = 'Internal Server Error'
    
    http_error = requests.exceptions.HTTPError("500 Server Error: Internal Server Error")
    http_error.response = response
    response.raise_for_status.side_effect = http_error
    
    mock_get.return_value = response
    yield mock_get



@pytest.fixture
def mock_line_api():
  """LINE API モック"""
  with patch('authentication.services.social_login_service.requests.get') as mock_get, \
      patch('authentication.services.social_login_service.jwt.decode') as mock_jwt:
    
    def get_side_effect(url, *args, **kwargs):
      response = MagicMock()
      response.raise_for_status = MagicMock()
      
      if 'line.me/v2/profile' in url:
        response.json.return_value = {
          'userId': 'U1234567890abcdef',
          'displayName': '山田太郎',
          'pictureUrl': 'https://example.com/photo.jpg'
        }
      return response
    
    mock_get.side_effect = get_side_effect
    mock_jwt.return_value = {
      'sub': 'U1234567890abcdef',
      'email': 'test@example.com'
    }
    
    yield mock_get, mock_jwt


@pytest.fixture
def mock_line_api_no_picture():
  """LINE API モック（画像なし）"""
  with patch('authentication.services.social_login_service.requests.get') as mock_get, \
      patch('authentication.services.social_login_service.jwt.decode') as mock_jwt:
    
    def get_side_effect(url, *args, **kwargs):
      response = MagicMock()
      response.raise_for_status = MagicMock()
      
      if 'line.me/v2/profile' in url:
        response.json.return_value = {
          'userId': 'U1234567890abcdef',
          'displayName': '山田太郎'
        }
      return response
    
    mock_get.side_effect = get_side_effect
    mock_jwt.return_value = {
      'sub': 'U1234567890abcdef',
      'email': 'test@example.com'
    }
    
    yield mock_get, mock_jwt


@pytest.fixture
def mock_line_api_no_email():
  """LINE API モック（メールなし）"""
  with patch('authentication.services.social_login_service.requests.get') as mock_get, \
      patch('authentication.services.social_login_service.jwt.decode') as mock_jwt:
    
    def get_side_effect(url, *args, **kwargs):
      response = MagicMock()
      response.raise_for_status = MagicMock()
      
      if 'line.me/v2/profile' in url:
        response.json.return_value = {
          'userId': 'U1234567890abcdef',
          'displayName': '山田太郎',
          'pictureUrl': 'https://example.com/photo.jpg'
        }
      return response
    
    mock_get.side_effect = get_side_effect
    mock_jwt.return_value = {
      'sub': 'U1234567890abcdef'
    }
    
    yield mock_get, mock_jwt


@pytest.fixture
def mock_line_api_error_401():
  """LINE APIエラー 401 モック"""
  with patch('authentication.services.social_login_service.requests.get') as mock_get:
    response = MagicMock()
    response.status_code = 401
    response.reason = 'Unauthorized'
    
    http_error = requests.exceptions.HTTPError("401 Client Error: Unauthorized")
    http_error.response = response
    response.raise_for_status.side_effect = http_error
    
    mock_get.return_value = response
    yield mock_get

@pytest.fixture
def mock_line_api_invalid_id_token():
  """LINE 無効なIDトークン モック"""
  with patch('authentication.services.social_login_service.requests.get') as mock_get, \
      patch('authentication.services.social_login_service.jwt.decode') as mock_jwt:
    
    def get_side_effect(url, *args, **kwargs):
      response = MagicMock()
      response.raise_for_status = MagicMock()
      
      if 'line.me/v2/profile' in url:
        response.json.return_value = {
          'userId': 'U1234567890abcdef',
          'displayName': '山田太郎'
        }
      return response
    
    mock_get.side_effect = get_side_effect
    mock_jwt.side_effect = Exception("Invalid token")
    
    yield mock_get, mock_jwt

@pytest.fixture
def mock_social_apis():
  """LINE & Google API モック"""
  with patch('authentication.services.social_login_service.requests.get') as mock_get, \
    patch('authentication.services.social_login_service.jwt.decode') as mock_jwt:
    
    def get_side_effect(url, *args, **kwargs):
      response = MagicMock()
      response.raise_for_status = MagicMock()
      
      if 'line.me/v2/profile' in url:
        response.json.return_value = {
          'userId': 'U1234567890abcdef',
          'displayName': '山田太郎',
          'pictureUrl': 'https://example.com/photo.jpg'
        }
      elif 'googleapis.com' in url:
        response.json.return_value = {
          'id': '123456789',
          'email': 'test@example.com',
          'given_name': '太郎',
          'family_name': '山田',
          'name': '山田太郎',
          'picture': 'https://example.com/photo.jpg',
          'verified_email': True
        }
      return response
    mock_get.side_effect = get_side_effect
    mock_jwt.return_value = {
      'sub': 'U1234567890abcdef',
      'email': 'test@example.com'
    }
    
    yield mock_get, mock_jwt


@pytest.fixture
def mock_facebook_api():
  """Facebook API モック"""
  with patch('authentication.services.social_login_service.requests.get') as mock_get:
    def side_effect(url, *args, **kwargs):
      response = MagicMock()
      response.raise_for_status = MagicMock()
      
      if 'graph.facebook.com' in url:
        response.json.return_value = {
          'id': 'fb123456789',
          'email': 'test@example.com',
          'email_verified': True,
          'first_name': '太郎',
          'last_name': '山田',
          'name': '山田太郎',
          'picture': {
            'data': {
              'url': 'https://example.com/photo.jpg'
            }
          }
        }
      return response
    
    mock_get.side_effect = side_effect
    yield mock_get

@pytest.fixture
def mock_facebook_api_no_email():
  """Facebook API モック NO EMAIL"""
  with patch('authentication.services.social_login_service.requests.get') as mock_get:
    def side_effect(url, *args, **kwargs):
      response = MagicMock()
      response.raise_for_status = MagicMock()
      
      if 'graph.facebook.com' in url:
        response.json.return_value = {
          'id': 'fb123456789',
          'first_name': '太郎',
          'last_name': '山田',
          'name': '山田太郎',
          'picture': {
            'data': {
              'url': 'https://example.com/photo.jpg'
            }
          }
        }
      return response
    
    mock_get.side_effect = side_effect
    yield mock_get


@pytest.fixture
def query_counter():
  """クエリ数をカウントし、詳細を表示するヘルパー"""
  class QueryCounter:
    def __init__(self):
      self.context = None
      self.queries = []
    
    def __enter__(self):
      self.context = CaptureQueriesContext(connection)
      self.context.__enter__()
      return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
      self.context.__exit__(exc_type, exc_val, exc_tb)
      self.queries = self.context.captured_queries
    
    @property
    def count(self):
      return len(self.queries)
    
    def print_queries(self):
      print(f"\n{'='*70}")
      print(f"実行されたクエリ数: {self.count}")
      print(f"{'='*70}")
      for i, query in enumerate(self.queries, 1):
        print(f"\n[クエリ {i}]")
        print(f"SQL: {query['sql']}")
        print(f"時間: {query['time']}秒")
      print(f"{'='*70}\n")
    
    def assert_max_queries(self, max_count, message=None):
      if self.count > max_count:
        self.print_queries()
        msg = message or f"クエリ数が多すぎます: {self.count} > {max_count}"
        raise AssertionError(msg)
  
  return QueryCounter()