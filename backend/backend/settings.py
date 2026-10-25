"""
Django settings for backend project.

ساختار:
  D:\\Projects\\RC_Amirkabir\\backend\\          ← manage.py
  ├── .env
  ├── accounts/ core/ events/ guides/ courses/ sitesettings/ managements/
  └── backend/                                    ← پکیج جنگو
      ├── __init__.py
      ├── settings.py (این فایل)
      ├── urls.py
      ├── asgi.py
      └── wsgi.py

پس BASE_DIR = دو سطح بالاتر از این فایل = backend/  (کنار manage.py).
و ماژول‌ها با پیشوند backend. شناخته می‌شوند.
"""
import os
from datetime import timedelta
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

# دو سطح بالاتر: backend/backend/settings.py → backend/
BASE_DIR = Path(__file__).resolve().parent.parent

# .env را در backend/.env یا backend/backend/.env جستجو کن
for _env_path in (BASE_DIR / '.env', BASE_DIR / 'backend' / '.env'):
    if _env_path.is_file():
        load_dotenv(_env_path)
        break


# =============================================================================
# امنیت پایه
# =============================================================================
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    raise ImproperlyConfigured(
        'DJANGO_SECRET_KEY در .env تعریف نشده است. '
        f'مسیرهای بررسی‌شده: {BASE_DIR / ".env"}, {BASE_DIR / "backend" / ".env"}. '
        'مطمئن شوید فایل .env کنار manage.py است و خط '
        'DJANGO_SECRET_KEY=... دارد.'
    )

DEBUG = os.environ.get('DJANGO_DEBUG', 'False').lower() in ('1', 'true', 'yes')

_default_hosts = 'localhost,127.0.0.1'
ALLOWED_HOSTS = [
    h.strip()
    for h in os.environ.get('DJANGO_ALLOWED_HOSTS', _default_hosts).split(',')
    if h.strip()
]

TRUSTED_PROXIES = [
    p.strip()
    for p in os.environ.get('TRUSTED_PROXIES', '').split(',')
    if p.strip()
]


# =============================================================================
# Authentication
# =============================================================================
AUTH_USER_MODEL = 'accounts.CustomUser'

AUTHENTICATION_BACKENDS = [
    'accounts.backends.EmailOrPhoneBackend',
    'django.contrib.auth.backends.ModelBackend',
]


# =============================================================================
# Apps (allauth حذف شد — احراز هویت از طریق JWT+OTP در accounts)
# =============================================================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_filters',
    'drf_spectacular',

    'core',
    'accounts',
    'events',
    'guides',
    'courses',
    'sitesettings',
    'managements',
    'quizes', 
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

# پکیج جنگو در backend/backend/ است، پس پیشوند backend. لازم است
ROOT_URLCONF = 'backend.urls'
WSGI_APPLICATION = 'backend.wsgi.application'
ASGI_APPLICATION = 'backend.asgi.application'


# =============================================================================
# Templates
# =============================================================================
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


# =============================================================================
# Database (env-overridable برای production)
# =============================================================================
DATABASES = {
    'default': {
        'ENGINE': os.environ.get('DB_ENGINE', 'django.db.backends.sqlite3'),
        'NAME': os.environ.get('DB_NAME', str(BASE_DIR / 'db.sqlite3')),
        'USER': os.environ.get('DB_USER', ''),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', ''),
        'PORT': os.environ.get('DB_PORT', ''),
    }
}


# =============================================================================
# CORS
# =============================================================================
CORS_ALLOWED_ORIGINS = [
    o.strip()
    for o in os.environ.get(
        'CORS_ALLOWED_ORIGINS',
        'http://localhost:5173,http://127.0.0.1:5173',
    ).split(',')
    if o.strip()
]
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = list(CORS_ALLOWED_ORIGINS)


# =============================================================================
# Django REST Framework
# =============================================================================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FormParser',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
        'otp': '10/hour',
        'download': '60/hour',
    },
}


# =============================================================================
# JWT
# =============================================================================
# توجه: ROTATE_REFRESH_TOKENS=True یعنی هر بار token/refresh/ صدا زده
# شود، refresh_token جدید برمی‌گردد و قدیمی blacklist می‌شود. فرانت
# باید مقدار جدید refresh را ذخیره کند وگرنه کاربر logout می‌شود.
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}


# =============================================================================
# Password validators
# =============================================================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# =============================================================================
# drf-spectacular (OpenAPI)
# =============================================================================
SPECTACULAR_SETTINGS = {
    'TITLE': 'RC_Amirkabir API',
    'DESCRIPTION': 'مستندات API پروژه RC_Amirkabir',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SERVE_PERMISSIONS': ['rest_framework.permissions.IsAdminUser'],
    'SERVE_AUTHENTICATION': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'COMPONENT_SPLIT_REQUEST': True,
    'SCHEMA_PATH_PREFIX': '/api/',
    'SORT_OPERATIONS': False,
    'APPEND_COMPONENTS': {
        'securitySchemes': {
            'jwtAuth': {
                'type': 'http', 'scheme': 'bearer', 'bearerFormat': 'JWT',
            }
        }
    },
}


# =============================================================================
# i18n
# =============================================================================
LANGUAGE_CODE = 'fa-ir'
TIME_ZONE = 'Asia/Tehran'
USE_I18N = True
USE_TZ = True


# =============================================================================
# Static / Media
# =============================================================================
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# =============================================================================
# Email
# =============================================================================
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@example.com')
SERVER_EMAIL = DEFAULT_FROM_EMAIL
EMAIL_BACKEND = os.environ.get(
    'EMAIL_BACKEND',
    'django.core.mail.backends.console.EmailBackend',
)


# =============================================================================
# Production security (فقط وقتی DEBUG=False)
# =============================================================================
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_HSTS_PRELOAD = False
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


# =============================================================================
# Logging
# =============================================================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {name} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {'handlers': ['console'], 'level': 'INFO'},
    'loggers': {
        'django.request': {
            'handlers': ['console'], 'level': 'ERROR', 'propagate': False,
        },
        'django.security': {
            'handlers': ['console'], 'level': 'ERROR', 'propagate': False,
        },
        'accounts': {
            'handlers': ['console'], 'level': 'INFO', 'propagate': False,
        },
        'managements': {
            'handlers': ['console'], 'level': 'INFO', 'propagate': False,
        },
    },
}


# =============================================================================
# Spectacular: docs فقط در dev عمومی، در prod فقط ادمین
# =============================================================================
# (SERVE_PERMISSIONS پیش‌فرض مقدار prod است؛ در DEBUG override می‌شود
# تا توسعه‌دهنده بدون لاگین به /api/docs/ دسترسی داشته باشد.)
if DEBUG:
    SPECTACULAR_SETTINGS['SERVE_PERMISSIONS'] = [
        'rest_framework.permissions.AllowAny',
    ]
    SPECTACULAR_SETTINGS['SERVE_AUTHENTICATION'] = []