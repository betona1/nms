import os
from pathlib import Path
from dotenv import load_dotenv
import pymysql

pymysql.version_info = (2, 2, 1, 'final', 0)
pymysql.install_as_MySQLdb()

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-nms-dev-key')
DEBUG = os.getenv('DEBUG', 'true').lower() in ('true', '1')
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '*').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'nms',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME', 'nms'),
        'HOST': os.getenv('DB_HOST', '192.168.219.200'),
        'PORT': int(os.getenv('DB_PORT', 3306)),
        'USER': os.getenv('DB_USER', 'root'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'OPTIONS': {'charset': 'utf8mb4'},
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'UNICODE_JSON': True,
}

CORS_ALLOW_ALL_ORIGINS = True

LANGUAGE_CODE = 'ko-kr'
TIME_ZONE = 'Asia/Seoul'
USE_I18N = True
USE_TZ = False

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# NMS
FIREBASE_KEY_PATH = os.getenv('FIREBASE_KEY_PATH', str(BASE_DIR / 'firebase-key.json'))
NMS_CHECK_INTERVAL = int(os.getenv('NMS_CHECK_INTERVAL', 60))
NMS_ALERT_COOLDOWN = int(os.getenv('NMS_ALERT_COOLDOWN', 300))
INTERNAL_API_KEY = os.getenv('INTERNAL_API_KEY', '')
CPM_BASE_URL = os.getenv('CPM_BASE_URL', 'http://192.168.219.100:9200')
CCTV_BASE_URL = os.getenv('CCTV_BASE_URL', 'http://192.168.219.100:8200')

# Oracle Cloud 중계 (Watch 8 앱 연동)
RELAY_URL = os.getenv('RELAY_URL', '')           # 예: http://134.185.104.140:8000
RELAY_API_KEY = os.getenv('RELAY_API_KEY', '')   # 공유 인증 키

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'nms': {'handlers': ['console'], 'level': 'INFO'},
    },
}
