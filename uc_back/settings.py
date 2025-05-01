from datetime import timedelta
import os
from pathlib import Path
import environ


# Env File setup.
env = environ.Env()
BASE_DIR = Path(__file__).resolve().parent.parent
dotenv_path = os.path.join(BASE_DIR, '.env')
if os.path.exists(dotenv_path):
    env.read_env(dotenv_path)


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")



# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*"]

CSRF_TRUSTED_ORIGINS = [
    "https://*.uc.co.uk",
    "http://localhost:3000",
    "http://192.168.0.180:3000",
    "http://localhost:8080",
    "https://*royalchauffeurservice.com",
    "https://www.royalchauffeurservice.com",
    "https://royalchauffeurservice.com/",
    "https://admin.uc.co.uk",
    "https://backend.uc.co.uk/",
]

CORS_ALLOWED_ORIGINS = [
    "https://example.com",
    "http://localhost:8080",
    "http://localhost:3000",
    "http://127.0.0.1:9000",
    "https://backend.uc.co.uk",
    "http://192.168.0.180:3000",
    "http://192.168.0.180:5000",
]

DRF_YASG_DEBUG = True


# Application definition
INSTALLED_APPS = [
    "daphne",
    # 'channels',
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    # 'django.contrib.gis',
    # 'broadcast',

    "rest_framework",
    "storages",
    "rest_framework_simplejwt.token_blacklist",
    
    'rest_framework.authtoken',
    "corsheaders",
    "simple_history",
    'drf_yasg',
    
    "mail_management",  # Mail Management App
    "notification_manager", # Notification Manager
    "client_app",
    "driver_app", #Driver App

    "organization_manager",
    "third_party_org_manager",
    "accounts",
    # "chat",
    # "trip",
    "subscription_management",
    "payment",
    "uc_admin",
    # "contact",
    "log",
    "django.contrib.sites",
    "django_celery_results",
    "django_celery_beat",

    "trip_management",
    "complaint_box",
    "location"

]

# Django all Custom auth Settings
SITE_ID = 1
AUTHENTICATION_BACKENDS = [
    "uc_back.custom_user_authentication.EmailBackend",  # Custom authentication backend
    'django.contrib.auth.backends.ModelBackend',        # Keep the default backend
]


# User Model
AUTH_USER_MODEL = "accounts.CustomUser"



MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "uc_back.custom_middlewares.JWTAuthenticationMiddleware",
    "uc_back.custom_middlewares.ActiveUserMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
]


# Django REST Framework- Set Authentication to Simple JWT configuration
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 8,
}



# CELERY CONFIGURATION
CELERY_BROKER_URL = env("REDIS_LOCATION")
CELERY_RESULT_BACKEND = "django-db"
CELERY_ACCEPT_CONTENT = ["application/json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "Asia/Dhaka"
CELERY_CACHE_BACKEND = "django-cache"

# CELERY BEAT CONFIGURATION
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"



# Simple JWT configuration (set up the timelines for the tokens)
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=8),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": False,
    "UPDATE_LAST_LOGIN": False,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "VERIFYING_KEY": None,
    "AUDIENCE": None,
    "ISSUER": None,
    "JWK_URL": None,
    "LEEWAY": 0,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "USER_AUTHENTICATION_RULE": "rest_framework_simplejwt.authentication.default_user_authentication_rule",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "TOKEN_USER_CLASS": "rest_framework_simplejwt.models.TokenUser",
    "JTI_CLAIM": "jti",
    "SLIDING_TOKEN_REFRESH_EXP_CLAIM": "refresh_exp",
    "SLIDING_TOKEN_LIFETIME": timedelta(days=7),
    "SLIDING_TOKEN_REFRESH_LIFETIME": timedelta(days=30),
}


# Templates
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            os.path.join(BASE_DIR, "templates"),
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# 1 day
ACCOUNT_LOGIN_ATTEMPTS_TIMEOUT = 86400

# or any other page
ACCOUNT_LOGOUT_REDIRECT_URL = "/accounts/login/"

ROOT_URLCONF = "uc_back.urls"
ASGI_APPLICATION = "uc_back.asgi.application"


# ================== Local Databse ======================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": env("DB_NAME"),
        "USER": env("DB_USER"),
        "PASSWORD": env("DB_PASSWORD"),
        "HOST": env("DB_HOST"),
        "PORT": env("DB_PORT"),
        'CONN_MAX_AGE': None,
        "OPTIONS": {
            'sslmode': 'require'
        },
    }
}





# ============ Stripe Account Setup ===============
STRIPE_SECRET_KEY = env("STRIPE_SECRET_KEY")
STRIPE_PUBLISHABLE_KEY = env("STRIPE_PUBLIC_KEY")
STRIPE_WEBHOOK_SECRET = env("STRIPE_WEBHOOK_SECRET")


# ============== Google Map API Setup =========
GOOGLE_API_KEY = env("GOOGLE_API_KEY")
AIRLABS_API_KEY = env("AIRLABS_API_KEY")


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "accounts.validators.CustomPasswordValidator",
    },
]




##================= Email Account Setup ====================
# Email Verification for ===Productions===
# # Zoho Mail Settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.zoho.com'
EMAIL_PORT = 587  # Use 465 for SSL if required
EMAIL_USE_TLS = True  # True for TLS, False for SSL
EMAIL_HOST_USER = env('EMAIL_HOST_USER')  # Authenticated account
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')  # Use app-specific password
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL')  # Group email address





# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# ==== Local Static files (CSS, JavaScript, Images)=======
STATIC_URL = '/static/'
MEDIA_ROOT = os.path.join(BASE_DIR, "media")
STATIC_ROOT = os.path.join(BASE_DIR, "static")
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Channel Configuration
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [env("REDIS_LOCATION")],
        },
    },
}


CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env("REDIS_LOCATION"),
    }
}



LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'uc_admin': { 
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}


USER_ONLINE_TIMEOUT = 300


USER_LASTSEEN_TIMEOUT = 60 * 60 * 24 * 7



PAYMENT_SUCCESS_URL = env('PAYMENT_SUCCESS_URL')
PAYMENT_CANCEL_URL = env('PAYMENT_CANCEL_URL')



CHECKOUT_SUCCESS_URL = env('CHECKOUT_SUCCESS_URL')
CHECKOUT_FAILED_URL = env('CHECKOUT_FAILED_URL')



LOGIN_REDIRECT_URL = "/django-admin/"
ADD_CARD_REDIRECT_URL = env("ADD_CARD_URL")


LICENSE_VERIFICATION_PORTAL_URL = env("LICENSE_VERIFICATION_PORTAL_URL")
COMPANY_NAME = "United Chauffeur"
ADMIN_PORTAL_URL = env("ADMIN_PORTAL_URL")


URL_TO_SEND_EMAIL_VERIFICATION_URL = env('URL_TO_SEND_EMAIL_VERIFICATION_URL')



# =========================== AWS Bucket Configuration========================
AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME")
AWS_S3_ENDPOINT_URL = env("AWS_S3_ENDPOINT_URL")
AWS_LOCATION = "UC-Folder"
AWS_S3_OBJECT_PARAMETERS = {"CacheControl": "max-age=86400"}
AWS_DEFAULT_ACL = "public-read"
AWS_S3_SIGNATURE_VERSION = "s3v4"
PUBLIC_MEDIA_LOCATION = "media"
DEFAULT_FILE_STORAGE = "uc_back.storage.PublicMediaStorage"



twilio_ac_ACCOUNT_SID = os.getenv("twilio_ac_ACCOUNT_SID")
twilio_ac_AUTH_TOKEN = os.getenv("twilio_ac_AUTH_TOKEN")
twilio_ac_VERIFY_SID = os.getenv("twilio_ac_VERIFY_SID")
twilio_ac_WHATSAPP_NUMBER = os.getenv("twilio_ac_WHATSAPP_NUMBER")


VEHICLE_VERIFICATION_API_URL = env("VEHICLE_VERIFICATION_API_URL")
VEHICLE_VERIFICATION_API_KEY = env("VEHICLE_VERIFICATION_API_KEY")

MOT_API_URL= env("MOT_API_URL")
MOT_API_KEY= env("MOT_API_KEY")
MICROSOFTONLINE_API = env("MICROSOFTONLINE_API")
MICROSOFTONLINE_CLIENT_ID = env("MICROSOFTONLINE_CLIENT_ID")
MICROSOFTONLINE_CLIENT_SECRET = env("MICROSOFTONLINE_CLIENT_SECRET")

# ====== Trusted Origins Setup Confiration=========

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = True

DISTANCE_CACHE_TIMEOUT = 60 * 60 * 24  # Cache for 24 hours
DISTANCE_TYPE_CACHE_TIMEOUT = 60 * 60 * 24 # Cache for 24 hours



