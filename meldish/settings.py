import os
from pathlib import Path
from datetime import timedelta
from decouple import config

# ===== 基本設定 =====

BASE_DIR = Path(__file__).resolve().parent.parent

# セキュリティ設定
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')

# Application definition

INSTALLED_APPS = [
  # Django標準アプリ
  'django.contrib.admin',
  'django.contrib.auth',
  'django.contrib.contenttypes',
  'django.contrib.sessions',
  'django.contrib.messages',
  'django.contrib.staticfiles',
  'django.contrib.sites',  # django-allauthに必要

  # 自作アプリ
  'core',
  
  # サードパーティアプリ
  'rest_framework',
  'rest_framework.authtoken',
  'rest_framework_simplejwt',
  'rest_framework_simplejwt.token_blacklist',
  'corsheaders',
  
  # 認証関連
  'dj_rest_auth',
  'dj_rest_auth.registration',
  'allauth',
  'allauth.account',
  'allauth.socialaccount',
  'allauth.socialaccount.providers.google',
  'allauth.socialaccount.providers.apple',
  
]


MIDDLEWARE = [
  'django.middleware.security.SecurityMiddleware',
  'corsheaders.middleware.CorsMiddleware',
  'django.contrib.sessions.middleware.SessionMiddleware',
  'django.middleware.locale.LocaleMiddleware',
  'django.middleware.common.CommonMiddleware',
  'django.middleware.csrf.CsrfViewMiddleware',
  'django.contrib.auth.middleware.AuthenticationMiddleware',
  'django.contrib.messages.middleware.MessageMiddleware',
  'django.middleware.clickjacking.XFrameOptionsMiddleware',
  'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'meldish.urls'


TEMPLATES = [
{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [BASE_DIR / 'templates'],
    'APP_DIRS': True,
    'OPTIONS': {
      'context_processors': [
        'django.template.context_processors.debug',
        'django.template.context_processors.request',
        'django.contrib.auth.context_processors.auth',
        'django.contrib.messages.context_processors.messages',
        'django.template.context_processors.i18n',
      ],
    },
  },
]

WSGI_APPLICATION = 'meldish.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
  'default': {
    'ENGINE': 'django.db.backends.mysql',
    'NAME': config('DB_NAME'),
    'USER': config('DB_USER'),
    'PASSWORD': config('DB_PASSWORD'),
    'HOST': config('DB_HOST'),   
    'PORT': config('DB_PORT'),
    'ATOMIC_REQUESTS': True,
    'CONN_MAX_AGE': 600,
  }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
  {
    'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
  },
  {
    'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    'OPTIONS': {
      'min_length': 8,
    }
  },
  {
    'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
  },
  {
    'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
  },
]

# ===== 国際化設定 =====

LANGUAGE_CODE = 'ja'

# サポートする言語
LANGUAGES = [
  ('ja', '日本語'),
  ('en', 'English'),
]

# 翻訳ファイルの場所
LOCALE_PATHS = [
  BASE_DIR / 'locale',
]

USE_I18N = True
USE_L10N = True

# タイムゾーン設定
TIME_ZONE = 'Australia/Brisbane'
USE_TZ = True 


# ===== 静的ファイル・メディアファイル =====

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'



# ===== カスタムユーザーモデル =====

AUTH_USER_MODEL = 'core.User'

# ===== サイトID（django-allauth用） =====

SITE_ID = 1

# ===== メール設定 =====

EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default=EMAIL_HOST_USER)

# ===== django-allauth設定 =====

AUTHENTICATION_BACKENDS = [
  # Django標準認証
  'django.contrib.auth.backends.ModelBackend',
  # allauth認証
  'allauth.account.auth_backends.AuthenticationBackend',
]

# アカウント設定
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_EMAIL_VERIFICATION = 'optional'
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 3
ACCOUNT_LOGIN_ATTEMPTS_LIMIT = 5
ACCOUNT_LOGIN_ATTEMPTS_TIMEOUT = 300
ACCOUNT_LOGOUT_ON_PASSWORD_CHANGE = True
ACCOUNT_UNIQUE_EMAIL = True

ACCOUNT_PASSWORD_RESET_TIMEOUT = 3600

# ソーシャル認証設定
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_VERIFICATION = 'none'

SOCIALACCOUNT_PROVIDERS = {
  'google': {
    'SCOPE': [
      'profile',
      'email',
    ],
    'AUTH_PARAMS': {
      'access_type': 'online',
    },
    'APP': {
      'client_id': os.environ.get('GOOGLE_WEB_CLIENT_ID', ''),
      'secret': os.environ.get('GOOGLE_CLIENT_SECRET', ''),
      'key': ''
    },
    'VERIFIED_EMAIL': True,
  },
  'apple': {
    'APP': {
      'client_id': config('APPLE_CLIENT_ID', default=''),
      'secret': config('APPLE_CLIENT_SECRET', default=''),
      'key': config('APPLE_KEY_ID', default=''),
      'certificate_key': config('APPLE_PRIVATE_KEY_PATH', default=''),
    },
    'SCOPE': ['name', 'email'],
  }
}

# Google認証用の追加設定（ネイティブアプリ用）
GOOGLE_OAUTH2_CLIENT_ID = os.environ.get('GOOGLE_WEB_CLIENT_ID', '')
GOOGLE_IOS_CLIENT_ID = os.environ.get('GOOGLE_IOS_CLIENT_ID', '')
GOOGLE_ANDROID_CLIENT_ID = os.environ.get('GOOGLE_ANDROID_CLIENT_ID', '')

# カスタムアダプター
SOCIALACCOUNT_FORMS = {
  'signup': 'your_app.forms.CustomSocialSignupForm',
}
SOCIALACCOUNT_ADAPTER = 'core.adapters.allauth_adapters.CustomSocialAccountAdapter'
ACCOUNT_ADAPTER = 'core.adapters.allauth_adapters.CustomAccountAdapter'

# ===== REST Framework設定 =====

REST_FRAMEWORK = {
  'DEFAULT_AUTHENTICATION_CLASSES': [
    'rest_framework_simplejwt.authentication.JWTAuthentication',
  ],
  'DEFAULT_PERMISSION_CLASSES': [
    'rest_framework.permissions.IsAuthenticated',
  ],
  'DEFAULT_RENDERER_CLASSES': [
    'rest_framework.renderers.JSONRenderer',
  ],
  'DEFAULT_THROTTLE_CLASSES': [
    'rest_framework.throttling.AnonRateThrottle',
    'rest_framework.throttling.UserRateThrottle',
  ],
  'DEFAULT_THROTTLE_RATES': {
    'anon': '100/hour',
    'user': '1000/hour',
    'login': '10/minute',
    'register': '10/hour',
  },
  'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
  'PAGE_SIZE': 20,
}

# 開発環境ではブラウザ表示も有効化
if DEBUG:
  REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'].append(
    'rest_framework.renderers.BrowsableAPIRenderer'
  )
  REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'].append(
    'rest_framework.authentication.SessionAuthentication'
  )

# ===== Simple JWT設定 =====

SIMPLE_JWT = {
  'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
  'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
  'ROTATE_REFRESH_TOKENS': True,
  'BLACKLIST_AFTER_ROTATION': True,
  'UPDATE_LAST_LOGIN': True,
  
  'ALGORITHM': 'HS256',
  'SIGNING_KEY': SECRET_KEY,
  'VERIFYING_KEY': None,
  
  'AUTH_HEADER_TYPES': ('Bearer',),
  'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
  'USER_ID_FIELD': 'id',
  'USER_ID_CLAIM': 'user_id',
  
  'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
  'TOKEN_TYPE_CLAIM': 'token_type',
}

# ===== dj-rest-auth設定 =====

REST_AUTH = {
  'USE_JWT': True,
  'JWT_AUTH_HTTPONLY': False,  # React Nativeではfalse
  'JWT_AUTH_COOKIE': None,
  'JWT_AUTH_REFRESH_COOKIE': None,
  'USER_DETAILS_SERIALIZER': 'accounts.serializers.UserSerializer',
  'REGISTER_SERIALIZER': 'accounts.serializers.RegisterSerializer',
  'LOGIN_SERIALIZER': 'accounts.serializers.CustomLoginSerializer',
}

# ===== CORS設定 =====

CORS_ALLOWED_ORIGINS = config(
  'CORS_ALLOWED_ORIGINS',
  default='http://localhost:19006,http://localhost:8081'
).split(',')

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
  'accept',
  'accept-encoding',
  'authorization',
  'content-type',
  'dnt',
  'origin',
  'user-agent',
  'x-csrftoken',
  'x-requested-with',
]

# ===== セキュリティ設定 =====

# 本番環境でのみ有効化
if not DEBUG:
  SECURE_SSL_REDIRECT = True
  SESSION_COOKIE_SECURE = True
  CSRF_COOKIE_SECURE = True
  SECURE_BROWSER_XSS_FILTER = True
  SECURE_CONTENT_TYPE_NOSNIFF = True
  SECURE_HSTS_SECONDS = 31536000
  SECURE_HSTS_INCLUDE_SUBDOMAINS = True
  SECURE_HSTS_PRELOAD = True
  X_FRAME_OPTIONS = 'DENY'

# セッション設定
SESSION_COOKIE_AGE = config('SESSION_COOKIE_AGE', default=1209600, cast=int)  # 2週間
SESSION_SAVE_EVERY_REQUEST = False
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# CSRF設定
CSRF_COOKIE_HTTPONLY = False  # JavaScriptからアクセス可能に
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_TRUSTED_ORIGINS = config(
  'CSRF_TRUSTED_ORIGINS',
  default='http://localhost:19006,http://localhost:8081,http://localhost:3000'
).split(',')


# ===== ロギング設定 =====

# logsディレクトリを作成
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

LOGGING = {
  'version': 1,
  'disable_existing_loggers': False,
  'formatters': {
    'verbose': {
      'format': '[{levelname}] {asctime} {module} {message}',
      'style': '{',
    },
    'simple': {
      'format': '{levelname} {message}',
      'style': '{',
    },
  },
  'filters': {
    'require_debug_false': {
      '()': 'django.utils.log.RequireDebugFalse',
    },
    'require_debug_true': {
      '()': 'django.utils.log.RequireDebugTrue',
    },
  },
  'handlers': {
    'console': {
      'level': 'INFO',
      'class': 'logging.StreamHandler',
      'formatter': 'simple',
    },
    'file': {
      'level': 'INFO',
      'class': 'logging.handlers.RotatingFileHandler',
      'filename': LOGS_DIR / 'django.log',
      'maxBytes': 1024 * 1024 * 10,  # 10MB
      'backupCount': 10,
      'formatter': 'verbose',
    },
    'security_file': {
      'level': 'WARNING',
      'class': 'logging.handlers.RotatingFileHandler',
      'filename': LOGS_DIR / 'security.log',
      'maxBytes': 1024 * 1024 * 10,
      'backupCount': 10,
      'formatter': 'verbose',
    },
  },
  'loggers': {
    'django': {
      'handlers': ['console', 'file'],
      'level': 'INFO',
      'propagate': False,
    },
    'accounts': {
      'handlers': ['console', 'file'],
      'level': 'DEBUG' if DEBUG else 'INFO',
      'propagate': False,
    },
    'security': {
      'handlers': ['security_file', 'console'],
      'level': 'WARNING',
      'propagate': False,
    },
  },
}

# ===== キャッシュ設定（Redis） =====

CACHES = {
  'default': {
    'BACKEND': 'django_redis.cache.RedisCache',
    'LOCATION': config('REDIS_URL', default='redis://127.0.0.1:6379/1'),
    'OPTIONS': {
      'CLIENT_CLASS': 'django_redis.client.DefaultClient',
    }
  }
}

# 開発環境ではダミーキャッシュ
if DEBUG:
  CACHES = {
    'default': {
      'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
  }

# ===== Celery設定（非同期タスク処理） =====

CELERY_BROKER_URL = config('REDIS_URL', default='redis://127.0.0.1:6379/0')
CELERY_RESULT_BACKEND = config('REDIS_URL', default='redis://127.0.0.1:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# ===== その他 =====

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
FRONTEND_WEB_URL = os.environ.get('FRONTEND_URL', default='http://localhost:3000')

if os.getenv("GITHUB_ACTIONS") == "true":
  DATABASES = {
    "default": {
      "ENGINE": "django.db.backends.mysql",
      "NAME": os.getenv("DB_NAME", "test_db"),
      "USER": os.getenv("DB_USER", "user"),
      "PASSWORD": os.getenv("DB_PASSWORD", "pass"),
      "HOST": os.getenv("DB_HOST", "127.0.0.1"),
      "PORT": "3306",
      "OPTIONS": {
          "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
      },
    }
  }