"""
テスト専用の設定ファイル
"""
from .settings import *

print("\n" + "=" * 80)
print("Loading settings_test.py")
print("=" * 80)

# ===================================
# Database - SQLiteに強制変更
# ===================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',  # メモリ上にDBを作成
    }
}

print(f"Database engine: {DATABASES['default']['ENGINE']}")

# ===================================
# Security - テスト用の設定
# ===================================
SECRET_KEY = 'test-secret-key-do-not-use-in-production-12345'
DEBUG = True
ALLOWED_HOSTS = ['*']

# ===================================
# Password Hashing - テストを高速化
# ===================================
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# ===================================
# Email - テスト用バックエンド
# ===================================
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# ===================================
# Cache - ダミーキャッシュ
# ===================================
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# ===================================
# Logging - テスト時は最小限に
# ===================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
}

print("=" * 80 + "\n")