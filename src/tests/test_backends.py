"""
Tests for django-stagedoor authentication backends.
"""

from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory

from stagedoor.backends import EmailTokenBackend, SMSTokenBackend, StageDoorBackend
from stagedoor.models import AuthToken, Email, PhoneNumber

if TYPE_CHECKING:
    from django.contrib.auth.models import User as UserType

    User = UserType
else:
    User = get_user_model()


@pytest.mark.django_db
class TestStageDoorBackend:
    """Test StageDoorBackend functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.backend = StageDoorBackend()
        self.factory = RequestFactory()

    def test_get_user_success(self):
        """Test getting a user by ID successfully."""
        user = User.objects.create_user(username="testuser", email="test@example.com")
        result = self.backend.get_user(user.pk)
        assert result == user

    def test_get_user_not_found(self):
        """Test getting a user that doesn't exist."""
        result = self.backend.get_user(99999)
        assert result is None

    def test_get_user_string_id(self):
        """Test getting a user with string ID."""
        user = User.objects.create_user(username="testuser", email="test@example.com")
        result = self.backend.get_user(str(user.pk))
        assert result == user

    def test_get_token_object_success(self):
        """Test getting a token object successfully."""
        email = Email.objects.create(email="test@example.com")
        token = AuthToken.objects.create(email=email, token="test-token")

        result = self.backend.get_token_object("test-token")
        assert result == token

    def test_get_token_object_not_found(self):
        """Test getting a token that doesn't exist."""
        result = self.backend.get_token_object("nonexistent-token")
        assert result is None

    def test_authenticate_no_token(self):
        """Test authentication with no token."""
        request = self.factory.get("/")
        result = self.backend.authenticate(request, token=None)
        assert result is None

    def test_authenticate_invalid_token(self):
        """Test authentication with invalid token."""
        request = self.factory.get("/")
        result = self.backend.authenticate(request, token="invalid-token")
        assert result is None

    def test_authenticate_with_existing_email_user(self):
        """Test authentication with existing email user."""
        user = User.objects.create_user(username="testuser", email="test@example.com")
        email = Email.objects.create(email="test@example.com", user=user)
        AuthToken.objects.create(email=email, token="test-token")

        request = self.factory.get("/")
        result = self.backend.authenticate(request, token="test-token")
        assert result == user

    def test_authenticate_with_existing_phone_user(self):
        """Test authentication with existing phone user."""
        user = User.objects.create_user(username="testuser", email="test@example.com")
        phone = PhoneNumber.objects.create(phone_number="+14155551234", user=user)
        AuthToken.objects.create(phone_number=phone, token="test-token")

        request = self.factory.get("/")
        result = self.backend.authenticate(request, token="test-token")
        assert result == user

    @patch("stagedoor.settings.SINGLE_USE_LINK", True)
    def test_authenticate_single_use_link(self):
        """Test authentication with single use link enabled."""
        user = User.objects.create_user(username="testuser", email="test@example.com")
        email = Email.objects.create(email="test@example.com", user=user)
        token = AuthToken.objects.create(email=email, token="test-token")

        request = self.factory.get("/")
        result = self.backend.authenticate(request, token="test-token")

        assert result == user
        # Token should be deleted
        assert not AuthToken.objects.filter(pk=token.pk).exists()

    @patch("stagedoor.settings.DISABLE_USER_CREATION", False)
    def test_authenticate_create_new_user_with_email(self):
        """Test authentication creates new user when enabled."""
        email = Email.objects.create(email="new@example.com")
        AuthToken.objects.create(email=email, token="test-token")

        request = self.factory.get("/")
        result = self.backend.authenticate(request, token="test-token")

        assert result is not None
        assert result.email == "new@example.com"  # type: ignore[attr-defined]
        assert result.username.startswith("u")  # type: ignore[attr-defined]

    @patch("stagedoor.settings.DISABLE_USER_CREATION", False)
    def test_authenticate_create_new_user_with_phone(self):
        """Test authentication creates new user with phone when enabled."""
        phone = PhoneNumber.objects.create(phone_number="+14155551234")
        AuthToken.objects.create(phone_number=phone, token="test-token")

        request = self.factory.get("/")
        result = self.backend.authenticate(request, token="test-token")

        assert result is not None
        assert result.username.startswith("u")  # type: ignore[attr-defined]

    @patch("stagedoor.settings.DISABLE_USER_CREATION", True)
    def test_authenticate_no_user_creation_disabled(self):
        """Test authentication returns None when user creation disabled and no existing user."""  # noqa: E501
        email = Email.objects.create(email="new@example.com")
        AuthToken.objects.create(email=email, token="test-token")

        request = self.factory.get("/")
        result = self.backend.authenticate(request, token="test-token")

        assert result is None

    def test_authenticate_with_next_url(self):
        """Test authentication sets next URL on user."""
        user = User.objects.create_user(username="testuser", email="test@example.com")
        email = Email.objects.create(email="test@example.com", user=user)
        AuthToken.objects.create(email=email, token="test-token", next_url="/dashboard")

        request = self.factory.get("/")
        result = self.backend.authenticate(request, token="test-token")

        assert result == user
        assert hasattr(result, "_stagedoor_next_url")
        assert result._stagedoor_next_url == "/dashboard"  # type: ignore

    @patch("stagedoor.settings.DISABLE_USER_CREATION", False)
    def test_authenticate_get_or_create_user(self):
        """Test that get_or_create is used for user creation."""
        email = Email.objects.create(email="duplicate@example.com")

        # Create first user
        AuthToken.objects.create(email=email, token="token1")
        request = self.factory.get("/")
        user1 = self.backend.authenticate(request, token="token1")

        # Associate email with user1
        email.user = user1
        email.save()

        # Create second token with same email
        AuthToken.objects.create(email=email, token="token2")
        user2 = self.backend.authenticate(request, token="token2")

        # Should return the same user
        assert user1 == user2


@pytest.mark.django_db
class TestEmailTokenBackend:
    """Test EmailTokenBackend functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.backend = EmailTokenBackend()
        self.factory = RequestFactory()

    def test_authenticate_no_token(self):
        """Test authentication with no token."""
        request = self.factory.get("/")
        result = self.backend.authenticate(request, token=None)
        assert result is None

    def test_authenticate_invalid_token(self):
        """Test authentication with invalid token."""
        request = self.factory.get("/")
        result = self.backend.authenticate(request, token="invalid-token")
        assert result is None

    def test_authenticate_token_no_email(self):
        """Test authentication with token that has no email."""
        phone = PhoneNumber.objects.create(phone_number="+14155551234")
        AuthToken.objects.create(phone_number=phone, token="test-token")

        request = self.factory.get("/")
        result = self.backend.authenticate(request, token="test-token")
        assert result is None

    def test_authenticate_success_updates_email_user(self):
        """Test successful authentication updates email user relationship."""
        User.objects.create_user(username="testuser", email="old@example.com")
        email = Email.objects.create(email="new@example.com")
        AuthToken.objects.create(email=email, token="test-token")

        request = self.factory.get("/")
        result = self.backend.authenticate(request, token="test-token")

        assert result is not None
        assert result.email == "new@example.com"  # type: ignore[attr-defined]
        email.refresh_from_db()
        assert email.user == result
        assert email.potential_user is None

    def test_authenticate_potential_user_mismatch(self):
        """Test authentication fails when potential user doesn't match."""
        user1 = User.objects.create_user(username="user1", email="user1@example.com")
        user2 = User.objects.create_user(username="user2", email="user2@example.com")
        email = Email.objects.create(email="test@example.com", potential_user=user1)
        AuthToken.objects.create(email=email, token="test-token")

        # Mock the parent authenticate to return user2 instead of user1
        with patch.object(StageDoorBackend, "authenticate", return_value=user2):
            request = self.factory.get("/")
            result = self.backend.authenticate(request, token="test-token")
            assert result is None

    @patch("stagedoor.settings.SINGLE_USE_LINK", True)
    def test_authenticate_single_use_link_deletes_token(self):
        """Test that single use link deletes token after authentication."""
        user = User.objects.create_user(username="testuser", email="test@example.com")
        email = Email.objects.create(email="test@example.com")
        token = AuthToken.objects.create(email=email, token="test-token")

        # Mock parent authenticate to return user
        with patch.object(StageDoorBackend, "authenticate", return_value=user):
            request = self.factory.get("/")
            result = self.backend.authenticate(request, token="test-token")

            assert result == user
            # Token should be deleted
            assert not AuthToken.objects.filter(pk=token.pk).exists()


@pytest.mark.django_db
class TestSMSTokenBackend:
    """Test SMSTokenBackend functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.backend = SMSTokenBackend()
        self.factory = RequestFactory()

    def test_authenticate_no_token(self):
        """Test authentication with no token."""
        request = self.factory.get("/")
        result = self.backend.authenticate(request, token=None)
        assert result is None

    def test_authenticate_invalid_token(self):
        """Test authentication with invalid token."""
        request = self.factory.get("/")
        result = self.backend.authenticate(request, token="invalid-token")
        assert result is None

    def test_authenticate_token_no_phone(self):
        """Test authentication with token that has no phone number."""
        email = Email.objects.create(email="test@example.com")
        AuthToken.objects.create(email=email, token="test-token")

        request = self.factory.get("/")
        result = self.backend.authenticate(request, token="test-token")
        assert result is None

    def test_authenticate_success_updates_phone_user(self):
        """Test successful authentication updates phone user relationship."""
        User.objects.create_user(username="testuser", email="test@example.com")
        phone = PhoneNumber.objects.create(phone_number="+14155551234")
        AuthToken.objects.create(phone_number=phone, token="test-token")

        request = self.factory.get("/")
        result = self.backend.authenticate(request, token="test-token")

        assert result is not None
        phone.refresh_from_db()
        assert phone.user == result
        assert phone.potential_user is None

    def test_authenticate_potential_user_mismatch(self):
        """Test authentication fails when potential user doesn't match."""
        user1 = User.objects.create_user(username="user1", email="user1@example.com")
        user2 = User.objects.create_user(username="user2", email="user2@example.com")
        phone = PhoneNumber.objects.create(
            phone_number="+14155551234", potential_user=user1
        )
        AuthToken.objects.create(phone_number=phone, token="test-token")

        # Mock the parent authenticate to return user2 instead of user1
        with patch.object(StageDoorBackend, "authenticate", return_value=user2):
            request = self.factory.get("/")
            result = self.backend.authenticate(request, token="test-token")
            assert result is None

    @patch("stagedoor.settings.SINGLE_USE_LINK", True)
    def test_authenticate_single_use_link_deletes_token(self):
        """Test that single use link deletes token after authentication."""
        user = User.objects.create_user(username="testuser", email="test@example.com")
        phone = PhoneNumber.objects.create(phone_number="+14155551234")
        token = AuthToken.objects.create(phone_number=phone, token="test-token")

        # Mock parent authenticate to return user
        with patch.object(StageDoorBackend, "authenticate", return_value=user):
            request = self.factory.get("/")
            result = self.backend.authenticate(request, token="test-token")

            assert result == user
            # Token should be deleted
            assert not AuthToken.objects.filter(pk=token.pk).exists()

    def test_authenticate_updates_user_phone_field(self):
        """Test authentication updates user phone_number field if it exists."""
        user = User.objects.create_user(username="testuser", email="test@example.com")
        phone = PhoneNumber.objects.create(phone_number="+14155551234")
        AuthToken.objects.create(phone_number=phone, token="test-token")

        # Mock parent authenticate to return user
        with patch.object(StageDoorBackend, "authenticate", return_value=user):
            request = self.factory.get("/")
            result = self.backend.authenticate(request, token="test-token")

            assert result == user
            phone.refresh_from_db()
            assert phone.user == user
