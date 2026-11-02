import re
import tempfile
from urllib.parse import urlsplit

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import PBKDF2PasswordHasher
from django.core import mail
from django.core.management import call_command
from django.test import Client, SimpleTestCase, TestCase, override_settings


class LegacyAccountTests(TestCase):
    def test_django_4_password_hash_still_allows_login(self):
        hasher = PBKDF2PasswordHasher()
        old_hash = hasher.encode("legacy-test-password", "test-salt", iterations=320000)
        user = get_user_model().objects.create(username="legacy-test", password=old_hash)
        client = Client(enforce_csrf_checks=True,
                        HTTP_HOST="nakit.asteriski.fi",
                        HTTP_X_FORWARDED_PROTO="https")
        self.assertEqual(client.get("/accounts/login/").status_code, 200)
        response = client.post("/accounts/login/", {
            "username": user.username,
            "password": "legacy-test-password",
            "csrfmiddlewaretoken": client.cookies["csrftoken"].value,
        }, HTTP_ORIGIN="https://nakit.asteriski.fi")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(int(client.session["_auth_user_id"]), user.pk)
        user.refresh_from_db()
        self.assertTrue(user.check_password("legacy-test-password"))


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class PasswordResetBehindProxyTests(TestCase):
    def test_reset_preserves_https_and_changes_only_the_requested_password(self):
        user = get_user_model().objects.create_user(
            "reset-test", "reset@example.invalid", "original-test-password"
        )
        client = Client(enforce_csrf_checks=True,
                        HTTP_HOST="nakit.asteriski.fi",
                        HTTP_X_FORWARDED_PROTO="https")
        page = client.get("/accounts/password_reset/")
        self.assertEqual(page.status_code, 200)
        response = client.post("/accounts/password_reset/", {
            "email": user.email,
            "csrfmiddlewaretoken": client.cookies["csrftoken"].value,
        }, HTTP_ORIGIN="https://nakit.asteriski.fi")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [user.email])
        link = re.search(r"https://nakit\.asteriski\.fi/\S+", mail.outbox[0].body)
        self.assertIsNotNone(link)
        user.refresh_from_db()
        self.assertTrue(user.check_password("original-test-password"))

        confirm = client.get(urlsplit(link.group()).path)
        self.assertEqual(confirm.status_code, 302)
        form_url = confirm["Location"]
        self.assertEqual(client.get(form_url).status_code, 200)
        result = client.post(form_url, {
            "new_password1": "replacement-test-password-482!",
            "new_password2": "replacement-test-password-482!",
            "csrfmiddlewaretoken": client.cookies["csrftoken"].value,
        }, HTTP_ORIGIN="https://nakit.asteriski.fi")
        self.assertEqual(result.status_code, 302)
        complete = client.get(result["Location"])
        self.assertContains(
            complete, '<a href="/accounts/login/">kirjautua</a>'
        )
        user.refresh_from_db()
        self.assertTrue(user.check_password("replacement-test-password-482!"))
        self.assertEqual(client.post("/accounts/login/", {
            "username": user.username,
            "password": "replacement-test-password-482!",
            "csrfmiddlewaretoken": client.cookies["csrftoken"].value,
        }, HTTP_ORIGIN="https://nakit.asteriski.fi").status_code, 302)
        self.assertEqual(int(client.session["_auth_user_id"]), user.pk)


class ContainerStaticTests(SimpleTestCase):
    def test_static_assets_are_served_with_debug_disabled(self):
        self.assertTrue(settings.SESSION_COOKIE_SECURE)
        with tempfile.TemporaryDirectory() as static_dir:
            with override_settings(DEBUG=False, STATIC_ROOT=static_dir):
                call_command("collectstatic", interactive=False, verbosity=0)
                client = Client(HTTP_HOST="nakit.asteriski.fi")
                for path in ("/static/css/hax.css", "/static/admin/css/base.css"):
                    response = client.get(path)
                    self.assertEqual(response.status_code, 200, path)
                    self.assertTrue(response["Content-Type"].startswith("text/css"))
                    response.close()
