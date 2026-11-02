# Temporary compatibility image for Django 4.0 / MariaDB 10.3; see DEPLOYMENT.md.
FROM python:3.9-slim-bookworm AS builder
WORKDIR /build
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

FROM python:3.9-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=nakitin3000.container_settings
WORKDIR /nakitin
RUN apt-get update \
    && apt-get install -y --no-install-recommends libmariadb3 \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 django \
    && useradd --uid 10001 --gid django --no-create-home django
COPY --from=builder /wheels /wheels
COPY requirements.txt .
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt \
    && rm -rf /wheels
COPY manage.py .
COPY nakit/ nakit/
COPY nakitin3000/ nakitin3000/
COPY templates/ templates/
COPY static/ static/
COPY deploy/entrypoint.sh /usr/local/bin/nakitin-entrypoint
RUN mkdir /nakitin/static_root && chown django:django /nakitin/static_root
USER django
EXPOSE 8000
ENTRYPOINT ["/bin/sh", "/usr/local/bin/nakitin-entrypoint"]
CMD ["gunicorn", "--workers=3", "--bind=0.0.0.0:8000", "--access-logfile=-", "--error-logfile=-", "--access-logformat=%(h)s %(s)s %(L)s", "nakitin3000.wsgi:application"]
