#!/bin/sh
set -eu

# Management commands remain explicit; startup must never migrate the database.
if [ "${1:-}" = "gunicorn" ]; then
    python manage.py check
    python manage.py collectstatic --noinput
fi
exec "$@"
