# Move Nakitin to the organization and Docker

Status: prepare and test only until a production database backup has been restored
successfully in isolation. No production data belongs in this repository or image.

## Ownership and baseline

The organization already owns https://github.com/asteriskiry/nakitin3000, a public
fork. The migration branch includes the deployed commit `5862b43` and preserves
the organization's existing history. Merge the reviewed migration PR there; do
not force-push or replace the organization's history. The old author's repository
can remain an optional read-only `upstream` remote.

Changing a Git remote does not restart the application or move its database. On
the existing app checkout, after verifying `git remote -v`:

```bash
git remote set-url origin https://github.com/asteriskiry/nakitin3000.git
git fetch origin
```

Do not pull into the running checkout yet. Use a separate clone for containers.
The production `settings.py` and `secret_key.txt` are ignored by Git and must be
backed up separately, including the now-working Brevo settings.

## Compatibility limit

This is a temporary container migration of the existing Python 3.9 / Django 4.0.1 /
Gunicorn 20.1.0 / mysqlclient 2.1.0 stack. These old runtime versions are not a
supported long-term production baseline. Containerization does not patch their
security issues. Plan a supported Python/Django/Gunicorn upgrade and database
upgrade next. Django 5.2 requires MariaDB 10.5 or newer; production is MariaDB
10.3.39. Do not silently upgrade the framework against the existing database.

Sources: [Django database support](https://docs.djangoproject.com/en/5.2/ref/databases/#mariadb-notes),
[Python version support](https://devguide.python.org/versions/).

## Runtime and persistent state

```text
asteriski-www (10.0.0.2): HTTPS Nginx
  -> asteriski-app (10.0.0.3):8000: Gunicorn in Docker
  -> asteriski-db (10.0.0.4):3306: existing nakitin database
```

The image contains application code, templates and static assets. It mounts the
private settings and the existing Django secret key read-only. This preserves
password hashes, sessions and the Brevo configuration. Database contents stay on
the existing database server. The app container never runs `migrate` or
`makemigrations` at startup. Restarting/replacing it does not recreate the database.

WhiteNoise serves collected CSS/admin assets from a disposable tmpfs. The existing
Nginx `try_files` may still serve files from `/srv/www/nakit.asteriski.fi` on the
web server; verify the CSS in the browser. If assets later change, sync that
directory or configure `/static/` to proxy to the app. Do not delete it blindly.
Gunicorn access logs omit request paths and query strings to avoid recording
password-reset tokens. Check Nginx's separate logging policy as well.

No FileField/ImageField exists in the checked application models. The live
MEDIA_ROOT was empty, but custom/private settings, server uploads, scheduled jobs
(including `deleteold`), and local files still need inventory before cutover.

## Stage without touching production

1. Securely back up the database, production settings, secret key and any local
   user files. Restore the database to a separate test database/server, compare
   table/row counts against the dump snapshot, and verify sample users/events/
   registrations. Keep a copy of the backup outside the database server.
2. Clone the organization repository into a new directory on `asteriski-app` and
   check out the reviewed migration commit. Do not replace the live checkout.
3. Copy `.env.example` to `.env`. Point its settings path to a **staging copy** of
   the live settings, with DATABASES changed to the isolated restored database,
   separate database credentials restricted to that database, and EMAIL_BACKEND
   set to `django.core.mail.backends.console.EmailBackend`. Do not send mail to
   restored users. Keep staging logs private because console mail includes reset
   links. Keep the bind address `127.0.0.1` and port `8001`.
4. Set NAKITIN_UID/GID to `id -u django` / `id -g django`. Both mounted files must
   be readable by that numeric user, ideally owned by django with mode 0600. Do
   not make secrets world-readable. Use a separate test secret in staging.

With Docker Engine and the Compose v2 plugin available:

```bash
docker compose config --quiet
docker compose build
docker compose run --rm nakitin python manage.py check
docker compose run --rm nakitin python manage.py migrate --check
docker compose up -d
curl --fail -H 'Host: nakit.asteriski.fi' http://127.0.0.1:8001/accounts/login/
curl --fail -H 'Host: nakit.asteriski.fi' http://127.0.0.1:8001/static/admin/css/base.css
docker compose logs --tail=50 nakitin
```

`migrate --check` reports pending migrations without applying them. If it fails,
stop and investigate; do not run migrations against production as a workaround.
Use a private HTTPS staging proxy for browser tests: session/CSRF cookies are
secure, so browser login over plain HTTP is intentionally unsuitable.

Confirm login, existing events/registrations, registration/cancellation and the
password-reset flow against staging. The automated tests use a disposable test
database; never invoke `manage.py test` with production credentials.

The container trusts `X-Forwarded-Proto` from Nginx for HTTPS reset links and CSRF.
Verify Nginx overwrites it using `proxy_set_header X-Forwarded-Proto $scheme` and
passes the public Host header. Restrict port 8000 to trusted private-network
clients (especially 10.0.0.2). Inspect Docker firewall behavior; a private bind
address alone is not an access-control rule.

## Cutover after backup/restore and staging verification

Record the old service definition and exact new Git commit/image ID. Take a final
consistent backup during a write pause. Keep the existing database and schema.
Stop the staging container. In `.env`, select the **production** settings/key paths,
set NAKITIN_BIND_IP=10.0.0.3 and NAKITIN_PORT=8000. The secret key must be the
original production value, not the staging value. Existing settings should retain
DEBUG=False, the public ALLOWED_HOSTS, HTTPS CSRF_TRUSTED_ORIGINS and Brevo SMTP.

```bash
docker compose down
docker compose config --quiet
docker compose run --rm nakitin python manage.py check
docker compose run --rm nakitin python manage.py migrate --check
sudo systemctl stop nakitin.service
docker compose up -d
docker compose ps
curl --fail -H 'Host: nakit.asteriski.fi' http://10.0.0.3:8000/accounts/login/
```

Check the public HTTPS site, account login, events and your own password-reset
email/link. Only once these pass, disable the old service's boot startup to avoid
a port conflict on reboot:

```bash
sudo systemctl disable nakitin.service
```

Keep its files/service available. Verify Docker is enabled at boot; Compose uses
`restart: unless-stopped`. No Nginx upstream change is needed for the same endpoint.

## Rollback

If container startup or verification fails, stop it before restarting Gunicorn:

```bash
docker compose down
sudo systemctl enable --now nakitin.service
```

Verify public HTTPS and logs. Because this migration keeps the existing database
and schema, writes made since cutover stay there. Do not restore an older database
over newer writes. This rollback recipe does not cover later schema migrations.

## Reproduce local tests with synthetic data

Use a disposable checkout and `.env` pointing to the absolute path of
`deploy/test-settings.py`, plus a private file containing a dummy test secret.
Leave UID/GID at 10001 and the loopback port default. The fixture uses SQLite and
in-memory email, with no production network access needed:

```bash
docker compose build
docker compose run --rm nakitin python manage.py test nakit --verbosity=2
```

These cover password reset through the HTTPS proxy header (including CSRF,
password change and login) and static/admin CSS with DEBUG disabled. Also test a
restored MariaDB database before production; SQLite tests alone cannot verify it.

Preparation validation: the image built successfully; both tests passed on
SQLite and a disposable MariaDB 10.3.39 server. Gunicorn/Compose startup, HTTP 200
for home/login/app CSS/admin CSS, absence of private settings/key from the image,
and no automatic database migrations were verified. `makemigrations --check
--dry-run` reported no changes. This used synthetic data, not a production restore.
