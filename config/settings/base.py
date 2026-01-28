"""
Django settings untuk PPDB System.
Settings ini adalah base configuration yang digunakan development & production.
"""
import os
from pathlib import Path
from decouple import config, Csv
from decimal import Decimal

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# =============================================================================
# SECURITY SETTINGS
# =============================================================================
SECRET_KEY = config('DJANGO_SECRET_KEY')
DEBUG = config('DJANGO_DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('DJANGO_ALLOWED_HOSTS', cast=Csv())

# =============================================================================
# APPLICATION DEFINITION
# =============================================================================
INSTALLED_APPS = [
    # Django Core
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third Party
    'crispy_forms',
    'crispy_bootstrap5',
    'django_cleanup',  # Auto-delete files ketika record dihapus
    
    # Local Apps
    'apps.accounts',
    'apps.registration',
    'apps.payments',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
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
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # Custom context processors
                'apps.registration.context_processors.registration_settings',
                'apps.registration.context_processors.contact_info'
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# =============================================================================
# DATABASE
# =============================================================================
DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE'),
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT'),
        'ATOMIC_REQUESTS': True,  # Semua request dalam transaction
        'CONN_MAX_AGE': 600,  # Connection pooling
    }
}

# =============================================================================
# AUTHENTICATION
# =============================================================================
AUTH_USER_MODEL = 'accounts.CustomUser'

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8}
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'registration:staff_dashboard'
LOGOUT_REDIRECT_URL = '/'

# =============================================================================
# INTERNATIONALIZATION
# =============================================================================
LANGUAGE_CODE = 'id'
TIME_ZONE = 'Asia/Jakarta'
USE_I18N = True
USE_TZ = True

# =============================================================================
# STATIC & MEDIA FILES
# =============================================================================
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = config('MEDIA_URL', default='/media/')
MEDIA_ROOT = config('MEDIA_ROOT', default=BASE_DIR / 'media')

# =============================================================================
# FILE UPLOAD SETTINGS (CRITICAL UNTUK KEAMANAN)
# =============================================================================
# Maximum upload size: 5MB
MAX_UPLOAD_SIZE = config('MAX_UPLOAD_SIZE', default=5242880, cast=int)

# Allowed file types
ALLOWED_DOCUMENT_TYPES = config(
    'ALLOWED_DOCUMENT_TYPES',
    default='pdf,jpg,jpeg,png',
    cast=Csv()
)

# File validation
FILE_UPLOAD_MAX_MEMORY_SIZE = MAX_UPLOAD_SIZE
DATA_UPLOAD_MAX_MEMORY_SIZE = MAX_UPLOAD_SIZE * 2

# =============================================================================
# CRISPY FORMS
# =============================================================================
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# =============================================================================
# PAYMENT GATEWAY CONFIGURATION
# =============================================================================
MIDTRANS_CONFIG = {
    'IS_PRODUCTION': config('MIDTRANS_IS_PRODUCTION', default=False, cast=bool),
    'SERVER_KEY': config('MIDTRANS_SERVER_KEY'),
    'CLIENT_KEY': config('MIDTRANS_CLIENT_KEY'),
    'MERCHANT_ID': config('MIDTRANS_MERCHANT_ID'),
    'WEBHOOK_SECRET': config('MIDTRANS_WEBHOOK_SECRET'),
}

# Payment Business Rules
REGISTRATION_FEE = config('REGISTRATION_FEE', default=500000, cast=Decimal)
# PAYMENT_EXPIRY_HOURS = config('PAYMENT_EXPIRY_HOURS', default=24, cast=int)
PAYMENT_MERCHANT_NAME = config('PAYMENT_MERCHANT_NAME', default='Yayasan Pendidikan')

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================
LOG_LEVEL = config('LOG_LEVEL', default='INFO')
LOG_DIR = BASE_DIR / 'logs'

# Create logs directory if not exists
LOG_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file_general': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_DIR / 'general.log',
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'file_payment': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_DIR / 'payment.log',
            'maxBytes': 1024 * 1024 * 10,
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'file_error': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_DIR / 'error.log',
            'maxBytes': 1024 * 1024 * 10,
            'backupCount': 10,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file_general'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        'apps.payments': {
            'handlers': ['console', 'file_payment', 'file_error'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'apps.registration': {
            'handlers': ['console', 'file_general', 'file_error'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
    },
}

# =============================================================================
# DEFAULT AUTO FIELD
# =============================================================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# =============================================================================
# SECURITY HEADERS (PRODUCTION)
# =============================================================================
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Payment Settings
REGISTRATION_FEE = 50000  # Rp 50.000
# PAYMENT_EXPIRY_HOURS = 24  # 24 jam

# ============================================
# CONTACT INFORMATION
# ============================================

CONTACT_INFO = {
    'whatsapp': '6281292127621',  # Format: 62xxx (tanpa +)
    'whatsapp_text': 'Halo Admin PPDB PKBM, saya ingin bertanya tentang pendaftaran.',
    'email': 'ppdb@pkbm.ac.id',
    'phone': '0812-9212-7621',
    'phone_raw': '+6281292127621',
    'address': 'Jl. Pendidikan No. 123, Jakarta',
    'office_hours': 'Senin - Jumat: 08.00 - 16.00 WIB | Sabtu: 08.00 - 12.00 WIB',
}