"""
Django settings for Kontra project.

Generated by 'django-admin startproject' using Django 4.1.3.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""
import os

from daphne.server import Server
from corsheaders.defaults import default_headers
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-vsn!!&^^y8@ydt&w_s%bpzh*w%@%$&3yvf+aub_lk$pp2*91dn'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["vaibhav123.a.pinggy.link","127.0.0.1","localhost"]




# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'daphne',
    'django.contrib.staticfiles',
    'accounts',
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.facebook',
    
    'channels',
    'dashboard',
    'django_celery_results',
    'corsheaders',
    'django_extensions',
    'dj_rest_auth',
    'rest_framework_simplejwt',
    'rest_framework.authtoken',
    'rest_framework',
    'payments',
    'sslserver',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    # 'dashboard.middleware.JWTAuthMiddleware1',
    

]

ROOT_URLCONF = 'Kontra.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'Kontra.wsgi.application'

ASGI_APPLICATION = 'Kontra.asgi.application'
# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'kontra',
        'USER': 'root',
        'PASSWORD': 'root',
        'HOST': 'localhost',  # Or the address of your MySQL server
        'PORT': '3306',       # Default port for MySQL
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# new additions


SITE_ID = 1

AUTHENTICATION_BACKENDS = (
 
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)

LOGIN_REDIRECT_URL = '/chat/'

ACCOUNT_LOGOUT_REDIRECT_URL = '/api/auths/login/'

# Social Authentication Settings
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': '906774570407-8o7dorrsvrjf24qig42l3th2296fv391.apps.googleusercontent.com',
            'secret': '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',
            'key': '',
        },
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'offline',
        },
        'OAUTH_PKCE_ENABLED': True,
    },
    'facebook': {
        'APP': {
            'client_id': '1503941530537849',
            'secret': 'd7c0cada2bca69910011b20a85ece3bc',
            'key': ''
        },
        'METHOD': 'oauth2',
        'SCOPE': ['email'],
        'FIELDS': [
            'id',
            'email',
            'name',
            'first_name',
            'last_name',
            'picture',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'VERIFIED_EMAIL': False,
    }
}

# dj-rest-auth + Allauth Integration for Social Login


# SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = '906774570407-8o7dorrsvrjf24qig42l3th2296fv391.apps.googleusercontent.com'
# SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = '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'

# SOCIAL_AUTH_FACEBOOK_KEY = '1503941530537849'
# SOCIAL_AUTH_FACEBOOK_SECRET = 'd7c0cada2bca69910011b20a85ece3bc'

SOCIALACCOUNT_ADAPTER = 'allauth.socialaccount.adapter.DefaultSocialAccountAdapter'
ACCOUNT_AUTHENTICATED_EMAIL = False # Allow email confirmation for social logins
# SOCIAL_AUTH_GOOGLE_OAUTH2_REDIRECT_URI = 'https://localhost:8000/accounts/google/login/callback/'
# SOCIAL_AUTH_FACEBOOK_OAUTH2_REDIRECT_URI = 'https://localhost:8000/accounts/facebook/login/callback/'
SOCIAL_AUTH_GOOGLE_OAUTH2_REDIRECT_URI = 'https://chatbot-zpj2tk.flutterflow.app/'
SOCIAL_AUTH_FACEBOOK_OAUTH2_REDIRECT_URI = 'https://chatbot-zpj2tk.flutterflow.app/'
# Email backend configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'  # e.g., 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'vaibhav@admirian.com'
EMAIL_HOST_PASSWORD = 'feir esah njde uqui'
EMAIL_USE_SSL = False 

# django-allauth settings
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_USERNAME_REQUIRED = False





CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}

import os
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_NAME = 'sessionid'

CDN_CUSTOM_DOMAIN_STATIC_IMG = 'https://static.admirian.com/'




# Celery settings
CELERY_BROKER_URL = 'redis://localhost:6379/0'  # Redis server URL
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

# Optional: Limit the number of concurrent workers
CELERY_WORKER_CONCURRENCY = 4  # Adjust based on server capacity

# Optional: Task acknowledgments and retry policies
CELERY_TASK_ACKS_LATE = True  # Acknowledge task only after completion
CELERY_TASK_REJECT_ON_WORKER_LOST = True  # Requeue task if worker is lost

# Optional: Task time limits to prevent resource exhaustion
CELERY_TASK_TIME_LIMIT = 300  # Max hard limit for task in seconds
CELERY_TASK_SOFT_TIME_LIMIT = 180  # Graceful limit in seconds before time-out

# Optional: Logging level for debugging
CELERYD_LOG_LEVEL = 'INFO'

# Optional: Define worker pool (use 'solo' for debugging in single-threaded environments)
CELERY_WORKER_POOL = 'solo'  # Default setting; change to 'solo' for local debugging

CORS_ALLOW_CREDENTIALS = True

# Define allowed origins for CORS
CORS_ALLOWED_ORIGINS = [
    "https://vaibhav123.a.pinggy.link",
    "https://app.flutterflow.io",
    "https://chatbot-homepage-1m5apq.flutterflow.app",
    "https://ff-debug-service-frontend-pro-ygxkweukma-uc.a.run.app",
    "http://localhost:8000", 
    "https://customwidgethosting.web.app",
    "https://chatbot-zpj2tk.flutterflow.app", 
    "http://127.0.0.1:8000",
  # Local testing
]

# Specify headers that can be exposed to the browser
CORS_EXPOSE_HEADERS = [
    'Authorization',  # So that the frontend can read the Authorization header
]

# Allow certain headers from frontend requests
from corsheaders.defaults import default_headers

CORS_ALLOW_HEADERS = list(default_headers) + [
    'Authorization',
    'X-CSRFToken',
    'X-Requested-With',
]
# CSRF settings (if still needed for forms, etc.)
CSRF_COOKIE_SECURE = False 
CSRF_COOKIE_REQUIRED = False # True for HTTPS
CSRF_COOKIE_SAMESITE = 'Lax'  # Allow cross-origin requests (only if still needed)
SESSION_COOKIE_SECURE = True  # Should be True if using HTTPS
SESSION_COOKIE_SAMESITE = 'None'  # Only if still using session cookies
SESSION_COOKIE_PATH = '/'  # Standard setting


REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}


# Simple JWT settings
from datetime import timedelta
PASSWORD_RESET_CONFIRM_URL = 'https://chatbot-zpj2tk.flutterflow.app/Passwordreset/{uid}/{token}/'
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=24),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}
FLUTTERFLOW_FRONTEND_URL = 'https://chatbot-zpj2tk.flutterflow.app'
# DJ Rest Auth additional settings

REST_AUTH = {
    'USE_JWT': True,
    'JWT_AUTH_RETURN_EXPIRATION': True,
    'TOKEN_MODEL': None,
    'SESSION_LOGIN': False,
    'OLD_PASSWORD_FIELD_ENABLED': True,
    'LOGOUT_ON_PASSWORD_CHANGE': False,
    # 'PASSWORD_RESET_SERIALIZER': 'accounts.serializers.CustomPasswordResetSerializer',
    'PASSWORD_RESET_CONFIRM_URL': f'{FLUTTERFLOW_FRONTEND_URL}/passwordreset/?uid={{uid}}&token={{token}}',
    # 'PASSWORD_RESET_USE_SITES_DOMAIN': False, 
    # Add these new settings
    'JWT_AUTH': {
        'JWT_AUTH_RETURN_EXPIRATION': True,
        'JWT_AUTH_REFRESH_TOKEN': True,
    }
}
REST_AUTH_SERIALIZERS = {
    "PASSWORD_RESET_SERIALIZER": "accounts.serializers.CustomPasswordResetSerializer",
}
REST_USE_JWT = True
JWT_AUTH_RETURN_EXPIRATION = True
REST_SESSION_LOGIN = False
# ACCOUNT_EMAIL_CONFIRMATION_URL = 'http://127.0.0.1:8000/api/auth/registration/verify-email?key={key}'



LOGOUT_ON_PASSWORD_CHANGE = False

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'dj_rest_auth': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}

PAYPAL_CLIENT_ID = 'AX21Ua2V18L5CaRHRkWWw6XkH4P5ogsR8wJYV5Vkc51gCkoX9lgCXBUHzECnXKigWC2wrzdccdJv_ME-'
PAYPAL_CLIENT_SECRET = 'EOTJxFS0ojMt9SdmaXW73xgDjLWmDzpqpBfqfrWjuh-rK0su4uUAudwES3z5rBso20u7T11j-saGhwei'
PAYPAL_MODE = 'sandbox'

CSRF_TRUSTED_ORIGINS = [
    "https://vaibhav123.a.pinggy.link","http://127.0.0.1:8000","https://chatbot-zpj2tk.flutterflow.app"
    # add other trusted origins here if needed
]

ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_EMAIL_CONFIRMATION_TEMPLATE = 'dashboard/templates/email_confirm.html'

FRONTEND_URL = 'https://chatbot-zpj2tk.flutterflow.app'



SOCIALACCOUNT_EMAIL_VERIFICATION = 'none' 
SOCIALACCOUNT_LOGIN_ON_GET = True
SITE_DOMAIN = 'https://chatbot-zpj2tk.flutterflow.app'
ACCOUNT_PASSWORD_RESET_CONFIRM_URL = 'passwordreset/?uid={uid}&token={token}'