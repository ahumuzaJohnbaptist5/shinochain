from decouple import config
from datetime import timedelta

SECRET_KEY = config("SECRET_KEY")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="*").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "storages",
    # Local apps
    "accounts",
    "videos",
    "social",
    "analytics",
    "worker",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "shinochain.urls"

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

WSGI_APPLICATION = "shinochain.wsgi.application"
ASGI_APPLICATION = "shinochain.asgi.application"

# Database
DATABASE_URL = config("DATABASE_URL", default="postgres://postgres:postgres@localhost:5432/shinochain")

def _parse_db_url(url):
    """Parse a postgres:// DATABASE_URL into Django DATABASES dict."""
    import urllib.parse
    r = urllib.parse.urlparse(url)
    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": r.path.lstrip("/"),
        "USER": r.username or "",
        "PASSWORD": r.password or "",
        "HOST": r.hostname or "localhost",
        "PORT": str(r.port or 5432),
        "CONN_MAX_AGE": 600,
    }

DATABASES = {"default": _parse_db_url(DATABASE_URL)}

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Django REST Framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.CursorPagination",
    "PAGE_SIZE": 20,
}

# SimpleJWT
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": False,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# CORS
CORS_ALLOWED_ORIGINS = config("FRONTEND_URL", default="http://localhost:3000").split(",")
CORS_ALLOW_CREDENTIALS = True

# Celery
CELERY_BROKER_URL = config("REDIS_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = config("REDIS_URL", default="redis://localhost:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"

# AWS / Cloudflare R2 (S3-compatible)
AWS_ACCESS_KEY_ID = config("AWS_ACCESS_KEY_ID", default="")
AWS_SECRET_ACCESS_KEY = config("AWS_SECRET_ACCESS_KEY", default="")
AWS_STORAGE_BUCKET_NAME = config("AWS_STORAGE_BUCKET_NAME", default="shinochain-videos")
AWS_S3_ENDPOINT_URL = config("AWS_S3_ENDPOINT_URL", default="")
AWS_S3_REGION_NAME = config("AWS_S3_REGION_NAME", default="auto")
AWS_S3_SIGNATURE_VERSION = "s3v4"
AWS_DEFAULT_ACL = None
AWS_S3_FILE_OVERWRITE = False

# Meilisearch
MEILISEARCH_URL = config("MEILISEARCH_URL", default="http://localhost:7700")
MEILISEARCH_MASTER_KEY = config("MEILISEARCH_MASTER_KEY", default="masterKey")
