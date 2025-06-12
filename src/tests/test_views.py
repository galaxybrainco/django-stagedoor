from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpResponse
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from stagedoor import settings as stagedoor_settings
from stagedoor.models import AuthToken, Email, PhoneNumber, generate_token_string
from stagedoor.views import login_post, token_post

TEST_EMAIL = "hello@hellocaller.app"
TEST_PHONE_NUMBER = "+14158675309"


class LoginPostTests(TestCase):
    def setup_request(self, request):
        request.user = AnonymousUser()

        def get_response():
            return HttpResponse()

        middleware = SessionMiddleware(get_response=get_response)  # type: ignore
        middleware.process_request(request)
        request.session.save()

        middleware = MessageMiddleware(get_response=get_response)  # type: ignore
        middleware.process_request(request)
        request.session.save()

    def test_happy_path_email(self):
        factory = RequestFactory()
        request = factory.post("/", {"email": TEST_EMAIL})
        self.setup_request(request)
        response = login_post(request)
        self.assertEqual(302, response.status_code)
        self.assertEqual(reverse("stagedoor:token-post"), response.url)  # type: ignore
        self.assertIsNotNone(Email.objects.filter(email=TEST_EMAIL).first())
        self.assertIsNotNone(AuthToken.objects.filter(email__email=TEST_EMAIL).first())

    def test_happy_path_phone(self):
        factory = RequestFactory()
        request = factory.post("/", {"phone_number": TEST_PHONE_NUMBER})
        self.setup_request(request)
        response = login_post(request)
        self.assertEqual(302, response.status_code)
        self.assertEqual(reverse("stagedoor:token-post"), response.url)  # type: ignore
        self.assertIsNotNone(
            PhoneNumber.objects.filter(phone_number=TEST_PHONE_NUMBER).first()
        )
        self.assertIsNotNone(
            AuthToken.objects.filter(
                phone_number__phone_number=TEST_PHONE_NUMBER
            ).first()
        )

    def test_happy_path_contact_phone(self):
        factory = RequestFactory()
        request = factory.post("/", {"contact": TEST_PHONE_NUMBER})
        self.setup_request(request)
        response = login_post(request)
        self.assertEqual(302, response.status_code)
        self.assertEqual(reverse("stagedoor:token-post"), response.url)  # type: ignore
        self.assertIsNotNone(
            PhoneNumber.objects.filter(phone_number=TEST_PHONE_NUMBER).first()
        )
        self.assertIsNotNone(
            AuthToken.objects.filter(
                phone_number__phone_number=TEST_PHONE_NUMBER
            ).first()
        )

    def test_happy_path_contact_email(self):
        factory = RequestFactory()
        request = factory.post("/", {"contact": TEST_EMAIL})
        self.setup_request(request)
        response = login_post(request)
        self.assertEqual(302, response.status_code)
        self.assertEqual(reverse("stagedoor:token-post"), response.url)  # type: ignore
        self.assertIsNotNone(Email.objects.filter(email=TEST_EMAIL).first())
        self.assertIsNotNone(AuthToken.objects.filter(email__email=TEST_EMAIL).first())

    def test_no_form_data(self):
        factory = RequestFactory()
        request = factory.post("/")
        self.setup_request(request)
        response = login_post(request)
        self.assertEqual(302, response.status_code)
        self.assertEqual(stagedoor_settings.LOGIN_URL, response.url)  # type: ignore
        self.assertEqual(0, len(Email.objects.all()))
        self.assertEqual(0, len(PhoneNumber.objects.all()))
        self.assertEqual(0, len(AuthToken.objects.all()))

    @override_settings(STAGEDOOR_ENABLE_EMAIL_OVERRIDE=True)
    def test_form_invalid_email(self):
        factory = RequestFactory()
        request = factory.post("/", {"email": "hi"})
        self.setup_request(request)
        response = login_post(request)
        self.assertEqual(302, response.status_code)
        self.assertEqual(stagedoor_settings.LOGIN_URL, response.url)  # type: ignore
        self.assertEqual(0, len(Email.objects.all()))
        self.assertEqual(0, len(PhoneNumber.objects.all()))
        self.assertEqual(0, len(AuthToken.objects.all()))

    def test_form_invalid_phone_contact(self):
        factory = RequestFactory()
        request = factory.post("/", {"contact": "hi"})
        self.setup_request(request)
        response = login_post(request)
        self.assertEqual(302, response.status_code)
        self.assertEqual(stagedoor_settings.LOGIN_URL, response.url)  # type: ignore
        self.assertEqual(0, len(Email.objects.all()))
        self.assertEqual(0, len(PhoneNumber.objects.all()))
        self.assertEqual(0, len(AuthToken.objects.all()))

    @override_settings(STAGEDOOR_ENABLE_EMAIL_OVERRIDE=True)
    @override_settings(STAGEDOOR_ENABLE_SMS_OVERRIDE=True)
    def test_email_and_phone(self):
        factory = RequestFactory()
        request = factory.post(
            "/", {"phone_number": TEST_PHONE_NUMBER, "email": TEST_EMAIL}
        )
        self.setup_request(request)
        response = login_post(request)
        self.assertEqual(302, response.status_code)
        self.assertEqual(reverse("stagedoor:token-post"), response.url)  # type: ignore
        self.assertIsNotNone(Email.objects.filter(email=TEST_EMAIL).first())
        self.assertIsNotNone(AuthToken.objects.filter(email__email=TEST_EMAIL).first())

    @override_settings(STAGEDOOR_ENABLE_EMAIL_OVERRIDE=True)
    def test_happy_path_redirect(self):
        factory = RequestFactory()
        request = factory.post("/?next=/next", {"email": TEST_EMAIL})
        self.setup_request(request)
        response = login_post(request)
        self.assertEqual(302, response.status_code)
        self.assertEqual(reverse("stagedoor:token-post"), response.url)  # type: ignore
        self.assertIsNotNone(Email.objects.filter(email=TEST_EMAIL).first())
        self.assertIsNotNone(AuthToken.objects.filter(email__email=TEST_EMAIL).first())
        self.assertEqual(
            "/next",
            AuthToken.objects.filter(email__email=TEST_EMAIL).first().next_url,  # type: ignore
        )

    @override_settings(STAGEDOOR_ENABLE_EMAIL_OVERRIDE=True)
    def test_email_exists(self):
        Email.objects.create(email=TEST_EMAIL)
        factory = RequestFactory()
        request = factory.post("/", {"email": TEST_EMAIL})
        self.setup_request(request)
        response = login_post(request)
        self.assertEqual(302, response.status_code)
        self.assertEqual(reverse("stagedoor:token-post"), response.url)  # type: ignore
        self.assertIsNotNone(Email.objects.get(email=TEST_EMAIL))
        self.assertIsNotNone(AuthToken.objects.filter(email__email=TEST_EMAIL).first())

    @override_settings(STAGEDOOR_ENABLE_SMS_OVERRIDE=True)
    def test_phone_number_exists(self):
        PhoneNumber.objects.create(phone_number=TEST_PHONE_NUMBER)
        factory = RequestFactory()
        request = factory.post("/", {"phone_number": TEST_PHONE_NUMBER})
        self.setup_request(request)
        response = login_post(request)
        self.assertEqual(302, response.status_code)
        self.assertEqual(reverse("stagedoor:token-post"), response.url)  # type: ignore
        self.assertIsNotNone(PhoneNumber.objects.get(phone_number=TEST_PHONE_NUMBER))
        self.assertIsNotNone(
            AuthToken.objects.filter(
                phone_number__phone_number=TEST_PHONE_NUMBER
            ).first()
        )


class TokenPostTests(TestCase):
    def setup_request(self, request):
        request.user = AnonymousUser()

        def get_response() -> HttpResponse:
            return HttpResponse()

        middleware = SessionMiddleware(get_response=get_response)  # type: ignore
        middleware.process_request(request)
        request.session.save()

        middleware = MessageMiddleware(get_response=get_response)  # type: ignore
        middleware.process_request(request)
        request.session.save()

    def test_happy_path_email(self):
        email = Email.objects.create(email=TEST_EMAIL)
        token_string = generate_token_string()
        AuthToken.objects.create(email=email, token=token_string)

        num_users = len(get_user_model().objects.all())
        factory = RequestFactory()
        request = factory.post("/", {"token": token_string})
        self.setup_request(request)
        response = token_post(request)
        self.assertEqual(302, response.status_code)
        self.assertEqual(stagedoor_settings.LOGIN_REDIRECT, response.url)  # type: ignore
        self.assertEqual(num_users + 1, len(get_user_model().objects.all()))

    def test_bad_token(self):
        token_string = generate_token_string()

        num_users = len(get_user_model().objects.all())
        factory = RequestFactory()
        request = factory.post("/", {"token": token_string})
        self.setup_request(request)
        response = token_post(request)
        self.assertEqual(302, response.status_code)
        self.assertEqual(stagedoor_settings.LOGIN_URL, response.url)  # type: ignore
        self.assertEqual(num_users, len(get_user_model().objects.all()))

    def test_happy_path_render(self):
        factory = RequestFactory()
        request = factory.get("/")
        self.setup_request(request)
        response = token_post(request)
        self.assertEqual(200, response.status_code)

    def test_happy_path_redirect_url(self):
        num_users = len(get_user_model().objects.all())
        email = Email.objects.create(email=TEST_EMAIL)
        token_string = generate_token_string()
        AuthToken.objects.create(email=email, token=token_string, next_url="/next")
        factory = RequestFactory()
        request = factory.post("/", {"token": token_string})
        self.setup_request(request)
        response = token_post(request)
        self.assertEqual(302, response.status_code)
        self.assertEqual("/next", response.url)  # type: ignore
        self.assertEqual(num_users + 1, len(get_user_model().objects.all()))

    def test_happy_path_redirect_user_already_exists(self):
        num_users = len(get_user_model().objects.all())
        email = Email.objects.create(email=TEST_EMAIL)
        token_string = generate_token_string()
        AuthToken.objects.create(email=email, token=token_string, next_url="/next")
        factory = RequestFactory()
        request = factory.post("/", {"token": token_string})
        self.setup_request(request)
        response = token_post(request)
        self.assertEqual(302, response.status_code)
        self.assertEqual("/next", response.url)  # type: ignore
        self.assertEqual(num_users + 1, len(get_user_model().objects.all()))

        # Now try again, and make sure users haven't gone up.
        token_string = generate_token_string()
        AuthToken.objects.create(email=email, token=token_string, next_url="/othernext")
        request = factory.post("/", {"token": token_string})
        self.setup_request(request)
        response = token_post(request)
        self.assertEqual(302, response.status_code)
        self.assertEqual("/othernext", response.url)  # type: ignore
        self.assertEqual(num_users + 1, len(get_user_model().objects.all()))
