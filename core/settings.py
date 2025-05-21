import os, random, string
from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv
from str2bool import str2bool
from celery import Celery
from celery.schedules import crontab

load_dotenv()  # take environment variables from .env.

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    SECRET_KEY = ''.join(random.choice(string.ascii_lowercase) for i in range(32))

# Получение API ключей из переменных окружения
BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
BINANCE_API_SECRET = os.getenv('BINANCE_API_SECRET')

# Убедитесь, что они были получены корректно
if not BINANCE_API_KEY or not BINANCE_API_SECRET:
    raise ValueError("API ключи Binance не установлены в окружении")

# Получение API ключей Bybit из переменных окружения
BYBIT_API_KEY = os.getenv('BYBIT_API_KEY')
BYBIT_API_SECRET = os.getenv('BYBIT_API_SECRET')

# Убедитесь, что ключи существуют
if not BYBIT_API_KEY or not BYBIT_API_SECRET:
    raise ValueError("API ключи Bybit не установлены в окружении")

# Enable/Disable DEBUG Mode
DEBUG = str2bool(os.environ.get('DEBUG'))
#print(' DEBUG -> ' + str(DEBUG) ) 

# Docker HOST
ALLOWED_HOSTS = ['*']

# Add here your deployment HOSTS
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000',
    'http://localhost:5085',
    'http://127.0.0.1:8000',
    'http://127.0.0.1:5085',
    'http://metrics.tonantis.com',
    'https://metrics.tonantis.com',
]

#Render Context
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# Application definition

INSTALLED_APPS = [
    "daphne",
    "channels",
    'admin_adminlte.apps.AdminAdminlteConfig',
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_celery_beat",
    "rest_framework",
    "corsheaders",
    "home",
    "wildberries",
    "tradingpool",
    "notifications",
    "notification",

]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

#APPEND_SLASH = False

CORS_ORIGIN_ALLOW_ALL = True

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

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

ALLOWED_HOSTS = ['www.wildberries.ru', 'wildberries.ru', '127.0.0.1', 'metrics.tonantis.com', 'localhost']



ROOT_URLCONF = "core.urls"


HOME_TEMPLATES = os.path.join(BASE_DIR, 'templates')

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [HOME_TEMPLATES],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.unread_notifications",
            ],
        },
    },
]

ASGI_APPLICATION = 'core.asgi.application'
WSGI_APPLICATION = "core.wsgi.application"

# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DB_ENGINE = os.getenv('DB_ENGINE', None)
DB_USERNAME = os.getenv('DB_USERNAME', None)
DB_PASS = os.getenv('DB_PASS', None)
DB_HOST = os.getenv('DB_HOST', None)
DB_PORT = os.getenv('DB_PORT', None)
DB_NAME = os.getenv('DB_NAME', None)

if DB_ENGINE and DB_NAME and DB_USERNAME:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.' + DB_ENGINE,
            'NAME': DB_NAME,
            'USER': DB_USERNAME,
            'PASSWORD': DB_PASS,
            'HOST': DB_HOST,
            'PORT': DB_PORT,
        },
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'db.sqlite3',
        }
    }

# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=5),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
}


# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = "ru"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),
]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)

#if not DEBUG:
#    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_REDIRECT_URL = '/'

# Получаем тип среды
DJANGO_ENV = os.environ.get("DJANGO_ENV", "development")  # Значение по умолчанию - development

required_vars = ["EMAIL_HOST", "EMAIL_HOST_USER", "EMAIL_HOST_PASSWORD", "DEFAULT_FROM_EMAIL", "DEFAULT_TO_TEST_EMAIL"]
for var in required_vars:
    if os.environ.get(var) is None:
        raise ValueError(f"Missing required environment variable: {var}")
# Устанавливаем бэкенд для отправки писем в зависимости от типа среды
if DJANGO_ENV == 'production':
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Настройки email для SMTP, если среда продакшн
if DJANGO_ENV == 'production':
    EMAIL_HOST = os.environ.get("EMAIL_HOST")
    EMAIL_PORT = int(os.environ.get("EMAIL_PORT", 587))
    EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "True") == "True"  # Преобразование строки в bool
    EMAIL_USE_SSL = os.environ.get("EMAIL_USE_SSL", "False") == "True"  # Преобразование строки в bool
    EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
    EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")
    DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL")
    DEFAULT_TO_TEST_EMAIL = os.environ.get("DEFAULT_TO_TEST_EMAIL")


# Включение отладочного вывода для базы данных в settings.py
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOGS_DIR, 'django.log'),
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'celery_tasks': {
            'handlers': ['file'],
            'level': 'WARNING',
            'propagate': True,
        },
    },
}


CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

#Запуск Celery Beat вместе с worker'ом:
#bash
# celery -A django-adminlte worker -l info
# celery -A core worker -l info -B
#TODO: обработать устойчивость воркера, на случай его неожиданного завершения, чтобы все работало всегда
CELERY_BEAT_SCHEDULE = {
    'update_campaigns': {
        'task': 'wildberries.tasks.update_all_stores_campaigns',
        'schedule': crontab(minute='*/1', hour='*/1'),
    },
    'collect-campaign-statistics': {
        'task': 'wildberries.tasks.collect_campaign_statistics',
        'schedule': crontab(minute='*/1', hour='*/1'),
    },
    'collect-keyword-statistics': {
        'task': 'wildberries.tasks.collect_keyword_statistics',
        'schedule': 600.0,
    },
    'collect-auto-campaign-statistics': {
        'task': 'wildberries.tasks.collect_auto_campaign_statistics',
        'schedule': 60.0,
    },
    'run-monitoring': {
        'task': 'wildberries.tasks.run_monitoring',
        'schedule': 20.0,
    },
    'delete-stale-tasks': {
        'task': 'wildberries.tasks.delete_stale_tasks',
        'schedule': crontab(minute='*/10'),  # Каждые 10 минут
    },
    'check_and_update_unknown_symbols': {
        'task': 'tradingpool.tasks.check_and_update_unknown_symbols',
        'schedule': crontab(minute='*/10'),  # Каждые 10 минут
    },
}

CACHE_LOCATION_URL = os.getenv('CACHE_LOCATION_URL', 'redis://localhost:6379/0')
CACHE_BACKEND = os.getenv('CACHE_BACKEND', 'django_redis.cache.RedisCache')
CACHE_CLIENT = os.getenv('CACHE_CLIENT', 'django_redis.client.DefaultClient')

CACHES = {
    'default': {
        'BACKEND': CACHE_BACKEND,
        'LOCATION': CACHE_LOCATION_URL,
        'OPTIONS': {
            'CLIENT_CLASS': CACHE_CLIENT,
        }
    }
}

# Настройка канала
CHANNEL_LAYERS = {
    "default": {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
        # "BACKEND": "channels_redis.core.RedisChannelLayer",
        # "CONFIG": {
        #     "hosts": [("127.0.0.1", 6379)],  # Убедитесь, что Redis запущен
        # },
    },
}

# Pillow
MEDIA_URL = '/media/' # сделать через env
MEDIA_ROOT = os.path.join(BASE_DIR, 'media') # сделать через env