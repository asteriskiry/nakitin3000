"""Container overrides; private deployment settings are mounted at runtime."""

from .settings import *  # noqa: F403

DEBUG = False
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
STATIC_ROOT = "/nakitin/static_root"

# Nginx must overwrite X-Forwarded-Proto; expose this app only to trusted proxies.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Serve collected assets even when the proxy's separate static directory is stale.
MIDDLEWARE = list(MIDDLEWARE)  # noqa: F405
MIDDLEWARE.insert(
    MIDDLEWARE.index("django.middleware.security.SecurityMiddleware") + 1,
    "whitenoise.middleware.WhiteNoiseMiddleware",
)
