from django.contrib.auth import get_user_model
from django.test import TestCase

from stagedoor.backends import EmailTokenBackend, SMSTokenBackend, StageDoorBackend
from stagedoor.models import AuthToken, Email, PhoneNumber, generate_token_string


class StageDoorBackendTests(TestCase):
    def test_get_user_happy_path(self):
        backend = StageDoorBackend()
        user = get_user_model().objects.create()

        user_from_backend = backend.get_user(user_id=user.id)  # type: ignore

        self.assertEqual(user, user_from_backend)

    def test_get_user_no_user(self):
        backend = StageDoorBackend()
        user_from_backend = backend.get_user(user_id=7)
        self.assertEqual(None, user_from_backend)

    def test_authenticate_happy_path(self):
        backend = StageDoorBackend()
        token_string = generate_token_string()
        AuthToken.objects.create(token=token_string)

        user = backend.authenticate(None, token=token_string)

        self.assertIsNotNone(user)

    def test_authenticate_no_token(self):
        backend = StageDoorBackend()
        token_string = generate_token_string()

        user = backend.authenticate(None, token=token_string)

        self.assertIsNone(user)

    def test_single_use_token(self):
        backend = StageDoorBackend()
        user = get_user_model().objects.create()

        user_from_backend = backend.get_user(user_id=user.id)  # type: ignore

        self.assertEqual(user, user_from_backend)

        self.assertEqual(0, len(AuthToken.objects.all()))


class EmailBackendTests(TestCase):
    def test_happy_path(self):
        email = Email.objects.create(email="hello@hellocaller.app")
        token_string = generate_token_string()
        AuthToken.objects.create(email=email, token=token_string)

        backend = EmailTokenBackend()
        user = backend.authenticate(None, token=token_string)
        self.assertIsNotNone(user)
        self.assertEqual("hello@hellocaller.app", user.email)  # type: ignore
        email.refresh_from_db()
        self.assertEqual(user, email.user)

    def test_no_token(self):
        backend = EmailTokenBackend()
        user = backend.authenticate(None, token="hello@hellocaller.app")
        self.assertIsNone(user)

    def test_user_already_exists(self):
        email = Email.objects.create(email="hello@hellocaller.app")
        token_string = generate_token_string()
        AuthToken.objects.create(email=email, token=token_string)
        backend = EmailTokenBackend()
        user = backend.authenticate(None, token=token_string)
        self.assertIsNotNone(user)
        self.assertEqual("hello@hellocaller.app", user.email)  # type: ignore
        email.refresh_from_db()
        self.assertEqual(user, email.user)

        # Now try again, and make sure we get the same user
        token_string = generate_token_string()
        AuthToken.objects.create(email=email, token=token_string)
        user = backend.authenticate(None, token=token_string)
        email.refresh_from_db()
        self.assertIsNotNone(user)
        self.assertEqual("hello@hellocaller.app", user.email)  # type: ignore
        self.assertEqual(user, email.user)


class SMSBackendTests(TestCase):
    def test_happy_path(self):
        phone_number = PhoneNumber.objects.create(phone_number="+14158675309")
        token_string = generate_token_string(sms=True)
        AuthToken.objects.create(phone_number=phone_number, token=token_string)

        backend = SMSTokenBackend()
        user = backend.authenticate(None, token=token_string)
        self.assertIsNotNone(user)
        phone_number = PhoneNumber.objects.get(phone_number="+14158675309")
        self.assertEqual(user, phone_number.user)

    def test_no_token(self):
        backend = SMSTokenBackend()
        user = backend.authenticate(None, token="+14158675310")
        self.assertIsNone(user)

    def test_user_already_exists(self):
        phone_number = PhoneNumber.objects.create(phone_number="+14158675309")
        token_string = generate_token_string(sms=True)
        AuthToken.objects.create(phone_number=phone_number, token=token_string)
        backend = SMSTokenBackend()
        user = backend.authenticate(None, token=token_string)
        self.assertIsNotNone(user)
        phone_number = PhoneNumber.objects.get(phone_number="+14158675309")
        self.assertEqual(user, phone_number.user)

        # Now try again, and make sure we get the same user
        token_string = generate_token_string(sms=True)
        AuthToken.objects.create(phone_number=phone_number, token=token_string)
        user = backend.authenticate(None, token=token_string)
        self.assertIsNotNone(user)
        phone_number = PhoneNumber.objects.get(phone_number="+14158675309")
        self.assertEqual(user, phone_number.user)
