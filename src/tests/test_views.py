from typing import TYPE_CHECKING
from unittest.mock import Mock, patch

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpResponse
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse

from stagedoor import settings as stagedoor_settings
from stagedoor.models import AuthToken, Email, PhoneNumber, generate_token_string
from stagedoor.views import (
    LoginForm,
    login_post,
    process_token,
    token_post,
)

if TYPE_CHECKING:
    from django.contrib.auth.models import User as UserType

    User = UserType
else:
    User = get_user_model()

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

    def test_admin_approval(self):
        factory = RequestFactory()
        with patch("stagedoor.settings.REQUIRE_ADMIN_APPROVAL", True):
            request = factory.post("/", {"email": TEST_EMAIL})
            self.setup_request(request)
            response = login_post(request)
            self.assertEqual(302, response.status_code)
            self.assertEqual(reverse("stagedoor:approval-needed"), response.url)  # type: ignore


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


@pytest.mark.django_db
class TestLoginForm:
    """Test LoginForm functionality."""

    @patch("stagedoor.settings.ENABLE_EMAIL", True)
    @patch("stagedoor.settings.ENABLE_SMS", False)
    def test_form_email_only(self):
        """Test form with email only enabled."""
        form = LoginForm()
        assert "email" in form.fields
        assert "phone_number" not in form.fields
        assert form.fields["contact"].label == "Your email"

    @patch("stagedoor.settings.ENABLE_EMAIL", False)
    @patch("stagedoor.settings.ENABLE_SMS", True)
    def test_form_sms_only(self):
        """Test form with SMS only enabled."""
        form = LoginForm()
        assert "phone_number" in form.fields
        assert "email" not in form.fields
        assert form.fields["contact"].label == "Your phone number, ie +15555555555"

    @patch("stagedoor.settings.ENABLE_EMAIL", True)
    @patch("stagedoor.settings.ENABLE_SMS", True)
    def test_form_both_enabled(self):
        """Test form with both email and SMS enabled."""
        form = LoginForm()
        assert "email" in form.fields
        assert "phone_number" in form.fields
        assert form.fields["contact"].label == "Your phone number or email"

    def test_form_clean_valid_email_contact(self):
        """Test form validation with valid email in contact field."""
        form = LoginForm(data={"contact": "test@example.com", "next": "/dashboard"})
        assert form.is_valid()
        assert form.cleaned_data["email"] == "test@example.com"
        assert form.cleaned_data["phone_number"] is None

    def test_form_clean_valid_phone_contact(self):
        """Test form validation with valid phone in contact field."""
        form = LoginForm(data={"contact": "+14155551234", "next": "/dashboard"})
        assert form.is_valid()
        assert form.cleaned_data["phone_number"] == "+14155551234"
        assert form.cleaned_data["email"] is None

    def test_form_clean_explicit_email_field(self):
        """Test form validation with explicit email field."""
        form = LoginForm(
            data={
                "email": "explicit@example.com",
                "contact": "ignored",
                "next": "/dashboard",
            }
        )
        assert form.is_valid()
        assert form.cleaned_data["email"] == "explicit@example.com"

    def test_form_clean_explicit_phone_field(self):
        """Test form validation with explicit phone field."""
        form = LoginForm(
            data={
                "phone_number": "+14155551234",
                "contact": "ignored",
                "next": "/dashboard",
            }
        )
        assert form.is_valid()
        assert form.cleaned_data["phone_number"] == "+14155551234"

    def test_form_clean_invalid_contact(self):
        """Test form validation with invalid contact info."""
        form = LoginForm(data={"contact": "invalid-contact", "next": "/dashboard"})
        assert not form.is_valid()
        assert "Please use a valid email address or phone number." in str(form.errors)

    def test_form_clean_no_contact(self):
        """Test form validation with no contact info."""
        form = LoginForm(data={"next": "/dashboard"})
        assert not form.is_valid()


@pytest.mark.django_db
class TestProcessToken:
    """Test process_token view."""

    def setup_method(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()

    @patch("stagedoor.views.authenticate")
    @patch("stagedoor.views.django_login")
    @patch("stagedoor.settings.LOGIN_REDIRECT", "/default/")
    def test_process_token_success(self, mock_login, mock_authenticate):
        """Test successful token processing."""
        user = User.objects.create_user(username="testuser", email="test@example.com")
        mock_authenticate.return_value = user

        request = self.factory.get("/")
        request.user = AnonymousUser()
        request._messages = Mock()  # type: ignore

        with patch("stagedoor.views.messages"):
            response = process_token(request, "valid-token")

        mock_authenticate.assert_called_once_with(request, token="valid-token")
        mock_login.assert_called_once_with(request, user)
        assert response.status_code == 302
        assert response.url == "/default/"  # type: ignore

    @patch("stagedoor.views.authenticate")
    @patch("stagedoor.settings.LOGIN_URL", "/login/")
    def test_process_token_invalid(self, mock_authenticate):
        """Test processing invalid token."""
        mock_authenticate.return_value = None

        request = self.factory.get("/")
        request._messages = Mock()  # type: ignore

        with patch("stagedoor.views.messages"):
            response = process_token(request, "invalid-token")

        assert response.status_code == 302
        assert response.url == "/login/"  # type: ignore

    @patch("stagedoor.views.authenticate")
    @patch("stagedoor.views.django_login")
    def test_process_token_with_next_url(self, mock_login, mock_authenticate):
        """Test token processing with next URL from user."""
        user = User.objects.create_user(username="testuser", email="test@example.com")
        user._stagedoor_next_url = "/dashboard/"  # type: ignore
        mock_authenticate.return_value = user

        request = self.factory.get("/")
        request.user = AnonymousUser()
        request._messages = Mock()  # type: ignore

        with patch("stagedoor.views.messages"):
            response = process_token(request, "token-with-next")

        assert response.status_code == 302
        assert response.url == "/dashboard/"  # type: ignore
        # Next URL should be removed from user
        assert not hasattr(user, "_stagedoor_next_url")

    @patch("stagedoor.views.authenticate")
    def test_process_token_already_authenticated(self, mock_authenticate):
        """Test token processing when user already authenticated."""
        user = User.objects.create_user(username="testuser", email="test@example.com")
        mock_authenticate.return_value = user

        request = self.factory.get("/")
        request.user = user  # Already authenticated
        request._messages = Mock()  # type: ignore

        with (
            patch("stagedoor.views.messages"),
            patch("stagedoor.views.django_login") as mock_login,
        ):
            response = process_token(request, "valid-token")

        # Should not call login again
        mock_login.assert_not_called()
        assert response.status_code == 302


@pytest.mark.django_db
class TestTokenLogin:
    """Test token_login view."""

    def setup_method(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()

    @patch("stagedoor.views.process_token")
    def test_token_login_success(self, mock_process_token):
        """Test token login with valid token."""
        from stagedoor.views import token_login

        mock_response = Mock()
        mock_response.status_code = 302
        mock_process_token.return_value = mock_response

        request = self.factory.get("/")
        token_login(request, "test-token")

        mock_process_token.assert_called_once()
        # Token should be passed to process_token
        args = mock_process_token.call_args[0]
        assert args[1] == "test-token"


@pytest.mark.django_db
class TestLogout:
    """Test logout view."""

    def setup_method(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()

    @patch("stagedoor.views.django_logout")
    @patch("stagedoor.settings.LOGOUT_REDIRECT", "/home/")
    def test_logout_success(self, mock_logout):
        """Test successful logout."""
        from stagedoor.views import logout

        user = User.objects.create_user(username="testuser", email="test@example.com")
        request = self.factory.get("/")
        request.user = user
        request._messages = Mock()  # type: ignore

        with patch("stagedoor.views.messages"):
            response = logout(request)

        mock_logout.assert_called_once()
        assert response.status_code == 302
        assert response.url == "/home/"  # type: ignore


@pytest.mark.django_db
class TestApprovalNeeded:
    """Test approval_needed view."""

    def setup_method(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()

    def test_approval_needed_renders_template(self):
        """Test approval needed view renders template."""
        from stagedoor.views import approval_needed

        request = self.factory.get("/")
        response = approval_needed(request)
        assert response.status_code == 200


@pytest.mark.django_db
class TestAdditionalViewCoverage:
    """Additional tests to improve coverage."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = Client()
        self.factory = RequestFactory()

    def test_login_post_with_next_url_parsing(self):
        """Test login post parses next URL from query string."""
        factory = RequestFactory()
        request = factory.post("/?next=/dashboard", {"email": TEST_EMAIL})
        request.user = AnonymousUser()

        def get_response():
            return HttpResponse()

        middleware = SessionMiddleware(get_response=get_response)  # type: ignore
        middleware.process_request(request)
        request.session.save()

        middleware = MessageMiddleware(get_response=get_response)  # type: ignore
        middleware.process_request(request)
        request.session.save()

        with patch("stagedoor.views.email_login_link"):
            response = login_post(request)

        assert response.status_code == 302
        token = AuthToken.objects.filter(email__email=TEST_EMAIL).first()
        assert token
        assert token.next_url == "/dashboard"

    @patch("stagedoor.views.generate_token")
    def test_login_post_email_conflict(self, mock_generate_token):
        """Test login post when email conflicts with existing user."""
        mock_generate_token.return_value = None

        factory = RequestFactory()
        request = factory.post("/", {"email": TEST_EMAIL})
        request.user = AnonymousUser()

        def get_response():
            return HttpResponse()

        middleware = SessionMiddleware(get_response=get_response)  # type: ignore
        middleware.process_request(request)
        request.session.save()

        middleware = MessageMiddleware(get_response=get_response)  # type: ignore
        middleware.process_request(request)
        request.session.save()

        response = login_post(request)
        assert response.status_code == 302
        assert response.url == stagedoor_settings.LOGIN_URL  # type: ignore

    @patch("stagedoor.views.generate_token")
    def test_login_post_phone_conflict(self, mock_generate_token):
        """Test login post when phone conflicts with existing user."""
        mock_generate_token.return_value = None

        factory = RequestFactory()
        request = factory.post("/", {"phone_number": TEST_PHONE_NUMBER})
        request.user = AnonymousUser()

        def get_response():
            return HttpResponse()

        middleware = SessionMiddleware(get_response=get_response)  # type: ignore
        middleware.process_request(request)
        request.session.save()

        middleware = MessageMiddleware(get_response=get_response)  # type: ignore
        middleware.process_request(request)
        request.session.save()

        response = login_post(request)
        assert response.status_code == 302
        assert response.url == stagedoor_settings.LOGIN_URL  # type: ignore

    def test_token_post_no_post_data(self):
        """Test token_post with no POST data."""
        from stagedoor.views import token_post

        request = self.factory.post("/")
        request.POST = {}  # type: ignore
        response = token_post(request)
        assert response.status_code == 200

    def test_form_clean_prefers_explicit_fields(self):
        """Test that explicit fields take precedence over contact field."""
        form = LoginForm(
            data={
                "email": "explicit@example.com",
                "phone_number": "+14155551234",
                "contact": "contact@example.com",
            }
        )
        assert form.is_valid()
        # Email field should take precedence
        assert form.cleaned_data["email"] == "explicit@example.com"
        # Phone should be from explicit field
        assert form.cleaned_data["phone_number"] == "+14155551234"
