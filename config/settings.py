import os, environ
from datetime import timedelta
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


DEBUG = os.environ.get('DEBUG')
SECRET_KEY = os.environ.get('SECRET_KEY')

ALLOWED_HOSTS = ['*']
    # 'port-0-travelproject-umnqdut2blqqevwyb.sel4.cloudtype.app',  # Cloudtype 제공 도메인
    # '34.64.184.142',  # 아웃바운드 IP
    # '34.64.220.67',   # 아웃바운드 IPc
    # '34.64.112.246',  # 아웃바운드 IP
    # 'localhost',
    # '127.0.0.1',
    # 'web-adventure-time-lxhy8g9qc44319ad.sel5.cloudtype.app'
# ]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'chat',
    'rest_framework',
    'corsheaders',
    'channels',
    'daphne',
    'rest_framework_simplejwt', # 로그인 테스트
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CORS_ALLOW_HEADERS = [
    'authorization',
    'content-type',
    'x-csrftoken',
    'x-requested-with',
]

CORS_ALLOW_ALL_ORIGINS = True #테스트 후 False로 바꾸기

CORS_ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:5501",  # 브라우저가 열리는 로컬 서버
    "http://127.0.0.1:5501",  # 브라우저가 열리는 로컬 서버
    "http://127.0.0.1:8001",
    "http://localhost:8001",
    "https://port-0-travelproject-umnqdut2blqqevwyb.sel4.cloudtype.app",
    "https://port-0-travelproject-9zxht12blqj9n2fu.sel4.cloudtype.app",
    "https://web-adventure-time-lxhy8g9qc44319ad.sel5.cloudtype.app",
    "http://svc.sel4.cloudtype.app",
]

CSRF_TRUSTED_ORIGINS = [
    "https://port-0-travelproject-umnqdut2blqqevwyb.sel4.cloudtype.app",
    "https://port-0-travelproject-9zxht12blqj9n2fu.sel4.cloudtype.app",
    "https://web-adventure-time-lxhy8g9qc44319ad.sel5.cloudtype.app",
]

CORS_ALLOW_CREDENTIALS = True

ROOT_URLCONF = 'config.urls'

SIMPLE_JWT = { # 로그인 테스트
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [os.environ.get('REDIS_URL')],
        },
    },
}

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
        'level': 'DEBUG',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'channels': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

APPEND_SLASH = True

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db_data', 'db.sqlite3'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
SESSION_COOKIE_SECURE = False  # HTTPS를 통해서만 전송되는 세션 쿠키
CSRF_COOKIE_SECURE = False  # HTTPS를 통해서만 전송되는 CSRF 쿠키
CSRF_COOKIE_SAMESITE = 'None'  # 크로스 사이트 요청에서 CSRF 쿠키가 전송되도록 설정
SESSION_COOKIE_SAMESITE = 'None'  # 크로스 사이트 요청에서 세션 쿠키가 전송되도록 설정
