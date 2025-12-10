"""Nodebechukwu Ikem was here 😎"""

import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY")

DEBUG = os.getenv("DEBUG", "false").lower() == "true"

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split(",")

CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")
CORS_ALLOW_ALL_ORIGINS = DEBUG

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',

    "rest_framework",
    "drf_spectacular",
    "rest_framework_simplejwt",
    "corsheaders",
    "storages",

    "roles_permissions",
    "account",
    "base",
    "crm",
    'media',
    "notification",
    "location",
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    "whitenoise.middleware.WhiteNoiseMiddleware",
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'utils.middlewares.CustomExceptionMiddleware',
]

ROOT_URLCONF = 'core.urls'

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

WSGI_APPLICATION = 'core.wsgi.application'
STATIC_ROOT = str(BASE_DIR / 'staticfiles')
STATIC_URL = '/static/'

MEDIA_ROOT = os.path.join(BASE_DIR, "media")

STATICFILES_DIRS = [str(BASE_DIR / 'static'), ]

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

USE_TEST_DB = os.getenv("USE_TEST_DB", "false").lower() == "true"

if USE_TEST_DB:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql_psycopg2",
            "NAME": os.getenv("DB_NAME", ""),
            "USER": os.getenv("DB_USERNAME", ""),
            "PASSWORD": os.getenv("DB_PASSWORD", ""),
            "HOST": os.getenv("DB_HOST", ""),
            "PORT": os.getenv("DB_PORT", "5432"),
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

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = "account.User"

DEFAULT_PAGE_SIZE = os.getenv("DEFAULT_PAGE_SIZE", 10)

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'utils.middlewares.CustomJWTAuthentication',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': DEFAULT_PAGE_SIZE
}

SPECTACULAR_SETTINGS = {
    'TITLE': os.getenv("PROJECT_TITLE", ""),
    'DESCRIPTION': os.getenv("PROJECT_DESCRIPTION", ""),
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'CONTACT': {
        'name': 'Nodebechukwu Anthony Ikem',
    },
    'PERSIST_AUTHORIZATION': False
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=2),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=20),
    "UPDATE_LAST_LOGIN": True,
    "CHECK_USER_IS_ACTIVE": False,
    "USER_ID_FIELD": "user_id"
}

DEFAULT_CACHE_TIMEOUT = 600

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PREFIX = os.getenv("REDIS_PREFIX", "dbt")

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_HOST,
        "KEY_PREFIX": REDIS_PREFIX,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "CONNECTION_POOL_KWARGS": {}
        },
        "TIMEOUT": DEFAULT_CACHE_TIMEOUT
    }
}

BROKER_URL = REDIS_HOST

CELERY_BROKER_URL = BROKER_URL
CELERY_RESULT_BACKEND = BROKER_URL
CELERY_BACKEND_URL = BROKER_URL
CELERY_ACCEPT_CONTENT = ["application/json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_DEFAULT_QUEUE = REDIS_PREFIX
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

APP_INFO_DEFAULTS = {
    "app_logo_url": os.getenv("APP_LOGO_URL", ""),
    "app_name": os.getenv("APP_NAME"),
    "app_address": os.getenv("APP_SUPPORT_ADDRESS"),
    "app_email": os.getenv("APP_SUPPORT_EMAIL"),
    "app_phone_number": os.getenv("APP_SUPPORT_HOTLINE"),
    "app_support_url": os.getenv("APP_SUPPORT_URL")
}

SYSTEM_DEFAULT_EMAIL_RECIPIENTS = os.getenv("DEFAULT_EMAIL_RECIPIENTS")

APP_ENC_ENABLED = os.getenv("APP_ENC_ENABLED", "False").lower() == "true"
DEFAULT_PASSWORD = os.getenv("DEFAULT_PASSWORD")
DEFAULT_OTP = os.getenv("DEFAULT_OTP")

DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

# S3 bucket config
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID', '')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', '')
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
AWS_S3_CUSTOM_DOMAIN = '%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
}
AWS_S3_SIGNATURE_VERSION = 's3v4'
AWS_S3_REGION_NAME = os.getenv("AWS_S3_REGION_NAME", "")
AWS_S3_FILE_OVERWRITE = False
AWS_S3_VERIFY = True

AWS_LOCATION = 'static'

PUBLIC_MEDIA_LOCATION = 'static'
USES_S3_BUCKET = os.getenv('USES_S3_BUCKET', 'true').lower() == 'true'
MEDIA_URL = 'https://%s/%s/' % (AWS_S3_CUSTOM_DOMAIN, PUBLIC_MEDIA_LOCATION) if USES_S3_BUCKET else '/media/'
AWS_DEFAULT_ACL = None


DEFAULT_PROFILE_IMAGE = os.getenv("DEFAULT_PROFILE_IMAGE")

CSRF_TRUSTED_ORIGINS = os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",")

REQUIRE_BROKER_URL = True

RATELIMIT_EXCEPTION_CLASS = "utils.errors.RateLimitException"

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", None)
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", None)
ADMIN_PHONE_NUMBER = os.getenv("ADMIN_PHONE_NUMBER", None)

API_REQUEST_LOGGING_ENABLED = os.getenv("API_REQUEST_LOGGING_ENABLED", "false").lower() == "true"

# MailJet Settings
MJ_API_KEY = os.getenv("MJ_API_KEY")
MJ_API_SECRET = os.getenv("MJ_API_SECRET")

DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "")

# CLOUDINARY SETTINGS
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")
CLOUDINARY_API_NAME = os.getenv("CLOUDINARY_API_NAME")

SEND_EMAIL_VIA = os.getenv("SEND_EMAIL_VIA")

# Email config
EMAIL_BACKEND = 'django_smtp_ssl.SSLEmailBackend'
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
EMAIL_USE_SSL = True
EMAIL_PORT = os.getenv("EMAIL_PORT")
