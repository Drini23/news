"""
Django settings for football project.
"""

from pathlib import Path
import os

from dotenv import load_dotenv
import pymysql
import dj_database_url

pymysql.install_as_MySQLdb()

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")


# ------------------------------------------------------------------
# Core
# ------------------------------------------------------------------
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")

SECRET_KEY = os.getenv("SECRET_KEY")

ALLOWED_HOSTS = [
    "futbollal.com",
    "www.futbollal.com",
    "127.0.0.1",
    "localhost",
    ".railway.app",
    ".up.railway.app",
    "news-py88.onrender.com",
]

CSRF_TRUSTED_ORIGINS = [
    "https://*.railway.app",
    "https://*.up.railway.app",
    "https://news-py88.onrender.com",
    "https://futbollal.com",
    "https://www.futbollal.com",
]

# Railway terminates TLS at its proxy — Django needs to trust that header
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True

# Secure cookies only in production (not local http)
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG


# ------------------------------------------------------------------
# API keys
# ------------------------------------------------------------------
FOOTBALL_API = os.getenv("FOOTBALL_API")
NEWS_API = os.getenv("NEWS_API")
RAPID_API = os.getenv("RAPID_API_KEY")
S_ALL_SPORT_API = os.getenv("ALL_SPORT_API")
FOOTBALL_LIVE_STREAMING_API = os.getenv("FOOTBALL_LIVE_STREAMING_API")
TRANSFER_NEWS_API = os.getenv("TRANSFER_NEWS_API")
BIGBALLS_API_KEY = os.getenv("BIGBALLS_API_KEY")

# Stripe — test (local)
STRIPE_SECRET_KEY_TEST = os.getenv("STRIPE_SECRET_KEY_TEST")
STRIPE_PUBLISHABLE_KEY_TEST = os.getenv("STRIPE_PUBLISHABLE_KEY_TEST")
STRIPE_WEBHOOK_SECRET_TEST = os.getenv("STRIPE_WEBHOOK_SECRET_TEST")
STRIPE_RECURRING_PRICE_ID_TEST = os.getenv("STRIPE_RECURRING_PRICE_ID_TEST")
STRIPE_ONE_TIME_PRICE_ID_TEST = os.getenv("STRIPE_ONE_TIME_PRICE_ID_TEST")

# Stripe — live
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
STRIPE_RECURRING_PRICE_ID = os.getenv("STRIPE_RECURRING_PRICE_ID", "")
STRIPE_ONE_TIME_PRICE_ID = os.getenv("STRIPE_ONE_TIME_PRICE_ID", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")


# ------------------------------------------------------------------
# Apps & Middleware
# ------------------------------------------------------------------
INSTALLED_APPS = [
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "channels",
    "blog",
    "news",
    "rapid",
    "live_stream_api",
    "register",
    "index",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_ratelimit.middleware.RatelimitMiddleware",
]

ROOT_URLCONF = "football.urls"
WSGI_APPLICATION = "football.wsgi.application"
ASGI_APPLICATION = "football.asgi.application"


# ------------------------------------------------------------------
# Redis (Railway) — CACHES + CHANNEL_LAYERS
# ------------------------------------------------------------------
REDIS_URL = os.getenv("REDIS_URL")

if REDIS_URL:
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": REDIS_URL,
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "IGNORE_EXCEPTIONS": True,
                "CONNECTION_POOL_KWARGS": {"max_connections": 50},
                "SOCKET_CONNECT_TIMEOUT": 5,
                "SOCKET_TIMEOUT": 5,
            },
            "KEY_PREFIX": "futbollal",
        }
    }

    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {
                "hosts": [REDIS_URL],
                "capacity": 1500,
                "expiry": 10,
            },
        }
    }
else:
    # Local dev — no Redis running
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.dummy.DummyCache",
        }
    }
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer",
        }
    }

DJANGO_REDIS_IGNORE_EXCEPTIONS = True
DJANGO_REDIS_LOG_IGNORED_EXCEPTIONS = True


# ------------------------------------------------------------------
# Templates
# ------------------------------------------------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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


# ------------------------------------------------------------------
# Database
# ------------------------------------------------------------------
db_url = os.environ.get("DRINI_SQL", "")
if db_url:
    DATABASES = {
        "default": dj_database_url.parse(
            db_url,
            conn_max_age=600,
            engine="django.db.backends.mysql",
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# ------------------------------------------------------------------
# Password validation
# ------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# ------------------------------------------------------------------
# i18n
# ------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# ------------------------------------------------------------------
# Static & Media
# ------------------------------------------------------------------
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
MEDIA_ROOT.mkdir(parents=True, exist_ok=True)

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"