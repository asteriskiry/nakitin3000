"""Synthetic local/container test settings. Never use with production data."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = Path("secret_key.txt").read_text().strip()
DEBUG = True  # The container settings must override this.
ALLOWED_HOSTS = ["nakit.asteriski.fi", "localhost", "127.0.0.1", "testserver"]
CSRF_TRUSTED_ORIGINS = ["https://nakit.asteriski.fi"]
INSTALLED_APPS = [
    "django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes",
    "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles",
    "nakit",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "nakitin3000.urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.debug",
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": "/tmp/nakitin-test.sqlite3"}}
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
DEFAULT_FROM_EMAIL = "Nakitin test <test@example.invalid>"
LANGUAGE_CODE = "fi-fi"
TIME_ZONE = "Europe/Helsinki"
USE_TZ = True
LOGIN_REDIRECT_URL = "/"
