from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class AuthFlowTests(TestCase):
    def test_signup_creates_user_profile_and_logs_in(self):
        res = self.client.post(reverse("accounts:signup"), {
            "first_name": "Amina", "last_name": "Otieno", "username": "amina", "email": "amina@example.com",
            "phone": "0712000000", "password1": "Harvest-2024!", "password2": "Harvest-2024!", "is_seller": "on",
        })
        self.assertRedirects(res, reverse("store:home"))
        user = User.objects.get(username="amina")
        self.assertTrue(user.profile.is_seller)
        self.assertEqual(user.profile.phone, "0712000000")
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def test_signup_rejects_duplicate_email(self):
        User.objects.create_user("x", "dup@example.com", "Harvest-2024!")
        res = self.client.post(reverse("accounts:signup"), {
            "username": "y", "email": "DUP@example.com", "password1": "Harvest-2024!", "password2": "Harvest-2024!",
        })
        self.assertEqual(res.status_code, 200)
        self.assertFalse(User.objects.filter(username="y").exists())

    def test_login_with_username_or_email_and_logout(self):
        User.objects.create_user("kip", "kip@example.com", "Harvest-2024!")
        for ident in ("kip", "KIP@example.com"):
            with self.subTest(ident=ident):
                res = self.client.post(reverse("accounts:login"), {"username": ident, "password": "Harvest-2024!"})
                self.assertEqual(res.status_code, 302)
                self.assertIn("_auth_user_id", self.client.session)
                self.client.post(reverse("accounts:logout"))
                self.assertNotIn("_auth_user_id", self.client.session)

    def test_bad_login(self):
        User.objects.create_user("kip", "kip@example.com", "Harvest-2024!")
        res = self.client.post(reverse("accounts:login"), {"username": "kip", "password": "wrong"})
        self.assertEqual(res.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_login_redirects_to_next(self):
        User.objects.create_user("kip", "kip@example.com", "Harvest-2024!")
        res = self.client.post(reverse("accounts:login") + "?next=/orders/",
                               {"username": "kip", "password": "Harvest-2024!", "next": "/orders/"})
        self.assertRedirects(res, "/orders/")

    def test_account_update(self):
        user = User.objects.create_user("kip", "kip@example.com", "Harvest-2024!")
        self.client.force_login(user)
        self.client.post(reverse("accounts:account"), {
            "first_name": "Kip", "last_name": "Rono", "email": "kip@example.com", "phone": "0700", "county": "Nakuru",
            "town": "Njoro", "address": "Box 1",
        })
        user.refresh_from_db()
        self.assertEqual(user.last_name, "Rono")
        self.assertEqual(user.profile.county, "Nakuru")

    def test_password_reset_sends_email(self):
        User.objects.create_user("kip", "kip@example.com", "Harvest-2024!")
        self.client.post(reverse("accounts:password_reset"), {"email": "kip@example.com"})
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("/accounts/password/reset/", mail.outbox[0].body)
