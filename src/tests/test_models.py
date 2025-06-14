"""
Tests for django-stagedoor models.
"""

from datetime import timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.utils.timezone import now

from stagedoor.models import (
    AuthToken,
    Email,
    PhoneNumber,
    generate_token,
    generate_token_string,
)

User = get_user_model()


@pytest.mark.django_db
class TestEmailModel:
    """Test Email model functionality."""

    def test_email_creation(self):
        """Test creating an email object."""
        email = Email.objects.create(email="test@example.com")
        assert email.email == "test@example.com"
        assert email.user is None
        assert email.potential_user is None

    def test_email_with_user(self):
        """Test email with associated user."""
        user = User.objects.create_user(username="testuser", email="test@example.com")  # type: ignore
        email = Email.objects.create(email="test@example.com", user=user)
        assert email.user == user
        assert email.potential_user is None

    def test_email_with_potential_user(self):
        """Test email with potential user."""
        user = User.objects.create_user(username="testuser", email="test@example.com")  # type: ignore
        email = Email.objects.create(email="test@example.com", potential_user=user)
        assert email.user is None
        assert email.potential_user == user

    def test_email_str_representation(self):
        """Test string representation of email."""
        user = User.objects.create_user(username="testuser", email="test@example.com")  # type: ignore
        potential_user = User.objects.create_user(  # type: ignore
            username="potential", email="potential@example.com"
        )
        email = Email.objects.create(
            email="test@example.com", user=user, potential_user=potential_user
        )
        expected = f"test@example.com: {user} (Maybe: {potential_user})"
        assert str(email) == expected

    def test_email_unique_constraint(self):
        """Test that email addresses must be unique."""
        Email.objects.create(email="unique@example.com")

        with pytest.raises(Exception):  # IntegrityError  # noqa: B017
            Email.objects.create(email="unique@example.com")

    def test_email_cascade_delete_user(self):
        """Test that deleting user cascades to email."""
        user = User.objects.create_user(username="testuser", email="test@example.com")  # type: ignore
        email = Email.objects.create(email="test@example.com", user=user)

        user.delete()
        assert not Email.objects.filter(pk=email.pk).exists()

    def test_email_cascade_delete_potential_user(self):
        """Test that deleting potential user cascades to email."""
        user = User.objects.create_user(username="testuser", email="test@example.com")  # type: ignore
        email = Email.objects.create(email="test@example.com", potential_user=user)

        user.delete()
        assert not Email.objects.filter(pk=email.pk).exists()


@pytest.mark.django_db
class TestPhoneNumberModel:
    """Test PhoneNumber model functionality."""

    def test_phone_number_creation(self):
        """Test creating a phone number object."""
        phone = PhoneNumber.objects.create(phone_number="+14155551234")
        assert str(phone.phone_number) == "+14155551234"
        assert phone.user is None
        assert phone.potential_user is None

    def test_phone_number_with_user(self):
        """Test phone number with associated user."""
        user = User.objects.create_user(username="testuser", email="test@example.com")  # type: ignore
        phone = PhoneNumber.objects.create(phone_number="+14155551234", user=user)
        assert phone.user == user
        assert phone.potential_user is None

    def test_phone_number_str_representation(self):
        """Test string representation of phone number."""
        user = User.objects.create_user(username="testuser", email="test@example.com")  # type: ignore
        potential_user = User.objects.create_user(  # type: ignore
            username="potential", email="potential@example.com"
        )
        phone = PhoneNumber.objects.create(
            phone_number="+14155551234", user=user, potential_user=potential_user
        )
        expected = f"+14155551234: {user} (Maybe: {potential_user})"
        assert str(phone) == expected

    def test_phone_number_unique_constraint(self):
        """Test that phone numbers must be unique."""
        PhoneNumber.objects.create(phone_number="+14155551234")

        with pytest.raises(Exception):  # IntegrityError  # noqa: B017
            PhoneNumber.objects.create(phone_number="+14155551234")

    def test_phone_number_cascade_delete_user(self):
        """Test that deleting user cascades to phone number."""
        user = User.objects.create_user(username="testuser", email="test@example.com")  # type: ignore
        phone = PhoneNumber.objects.create(phone_number="+14155551234", user=user)

        user.delete()
        assert not PhoneNumber.objects.filter(pk=phone.pk).exists()


@pytest.mark.django_db
class TestAuthTokenModel:
    """Test AuthToken model functionality."""

    def test_auth_token_creation(self):
        """Test creating an auth token."""
        email = Email.objects.create(email="test@example.com")
        token = AuthToken.objects.create(email=email, token="test-token")
        assert token.token == "test-token"
        assert token.email == email
        assert token.phone_number is None
        assert token.next_url == ""
        assert token.approved is True

    def test_auth_token_with_phone_number(self):
        """Test creating token with phone number."""
        phone = PhoneNumber.objects.create(phone_number="+14155551234")
        token = AuthToken.objects.create(phone_number=phone, token="phone-token")
        assert token.phone_number == phone
        assert token.email is None

    def test_auth_token_with_next_url(self):
        """Test creating token with next URL."""
        email = Email.objects.create(email="test@example.com")
        token = AuthToken.objects.create(
            email=email, token="redirect-token", next_url="/dashboard"
        )
        assert token.next_url == "/dashboard"

    def test_auth_token_not_approved(self):
        """Test creating unapproved token."""
        email = Email.objects.create(email="test@example.com")
        token = AuthToken.objects.create(
            email=email, token="pending-token", approved=False
        )
        assert token.approved is False

    def test_auth_token_str_representation(self):
        """Test string representation of auth token."""
        email = Email.objects.create(email="test@example.com")
        token = AuthToken.objects.create(email=email, token="str-token")
        # Should return formatted timestamp
        expected_format = token.timestamp.strftime("%Y-%m-%d %H:%M:%S")  # type: ignore[attr-defined]
        assert str(token) == expected_format

    def test_delete_stale_tokens(self):
        """Test deletion of stale tokens."""
        email = Email.objects.create(email="test@example.com")

        # Create a fresh token
        fresh_token = AuthToken.objects.create(email=email, token="fresh-token")

        # Create a stale token by mocking its timestamp
        stale_token = AuthToken.objects.create(email=email, token="stale-token")

        # Manually set timestamp to be old
        old_time = now() - timedelta(seconds=3700)  # Older than default 3600 seconds
        AuthToken.objects.filter(pk=stale_token.pk).update(timestamp=old_time)

        # Delete stale tokens
        AuthToken.delete_stale()

        # Fresh token should still exist, stale token should be gone
        assert AuthToken.objects.filter(pk=fresh_token.pk).exists()
        assert not AuthToken.objects.filter(pk=stale_token.pk).exists()

    @patch("stagedoor.settings.TOKEN_DURATION", 1800)  # 30 minutes
    def test_delete_stale_with_custom_duration(self):
        """Test deletion of stale tokens with custom duration."""
        email = Email.objects.create(email="test@example.com")

        # Create token
        token = AuthToken.objects.create(email=email, token="custom-duration-token")

        # Set timestamp to be older than custom duration
        old_time = now() - timedelta(seconds=2000)  # Older than 1800 seconds
        AuthToken.objects.filter(pk=token.pk).update(timestamp=old_time)

        # Delete stale tokens
        AuthToken.delete_stale()

        # Token should be deleted
        assert not AuthToken.objects.filter(pk=token.pk).exists()

    def test_auth_token_cascade_delete_email(self):
        """Test that deleting email cascades to auth token."""
        email = Email.objects.create(email="test@example.com")
        token = AuthToken.objects.create(email=email, token="cascade-token")

        email.delete()
        assert not AuthToken.objects.filter(pk=token.pk).exists()

    def test_auth_token_cascade_delete_phone(self):
        """Test that deleting phone number cascades to auth token."""
        phone = PhoneNumber.objects.create(phone_number="+14155551234")
        token = AuthToken.objects.create(
            phone_number=phone, token="phone-cascade-token"
        )

        phone.delete()
        assert not AuthToken.objects.filter(pk=token.pk).exists()


class TestGenerateTokenString:
    """Test generate_token_string function."""

    def test_generate_email_token_default_length(self):
        """Test generating email token with default length."""
        with patch("stagedoor.settings.EMAIL_TOKEN_LENGTH", 32):
            token = generate_token_string()
            assert len(token) == 32
            # Should contain alphanumeric characters (excluding confusing ones)
            assert all(
                c in "abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ123456789"
                for c in token
            )

    def test_generate_sms_token(self):
        """Test generating SMS token."""
        with patch("stagedoor.settings.SMS_TOKEN_LENGTH", 6):
            token = generate_token_string(sms=True)
            assert len(token) == 6
            # Should contain only digits
            assert all(c in "123456789" for c in token)

    def test_token_randomness(self):
        """Test that tokens are random."""
        tokens = [generate_token_string() for _ in range(10)]
        # All tokens should be different
        assert len(set(tokens)) == 10

    @patch("stagedoor.settings.EMAIL_TOKEN_LENGTH", 8)
    @patch("stagedoor.settings.SMS_TOKEN_LENGTH", 4)
    def test_custom_token_lengths(self):
        """Test custom token lengths."""
        email_token = generate_token_string()
        sms_token = generate_token_string(sms=True)

        assert len(email_token) == 8
        assert len(sms_token) == 4


@pytest.mark.django_db
class TestGenerateToken:
    """Test generate_token function."""

    def test_generate_token_with_email(self):
        """Test generating token with email."""
        token = generate_token(email="test@example.com")

        assert token is not None
        assert token.email is not None
        assert token.email.email == "test@example.com"  # type: ignore[attr-defined]
        assert token.phone_number is None
        assert token.next_url == ""
        # Token should be saved to database
        assert AuthToken.objects.filter(token=token.token).exists()

    def test_generate_token_with_phone(self):
        """Test generating token with phone number."""
        token = generate_token(phone_number="+14155551234")

        assert token is not None
        assert token.phone_number is not None
        assert str(token.phone_number.phone_number) == "+14155551234"  # type: ignore[attr-defined]
        assert token.email is None
        # Token should be saved to database
        assert AuthToken.objects.filter(token=token.token).exists()

    def test_generate_token_with_next_url(self):
        """Test generating token with next URL."""
        token = generate_token(email="test@example.com", next_url="/dashboard")

        assert token is not None
        assert token.next_url == "/dashboard"

    def test_generate_token_no_contact_info(self):
        """Test generating token without email or phone."""
        token = generate_token()
        assert token is None

    def test_generate_token_existing_email(self):
        """Test generating token for existing email."""
        # Create existing email
        existing_email = Email.objects.create(email="existing@example.com")

        token = generate_token(email="existing@example.com")

        assert token is not None
        assert token.email == existing_email
        # Email count should still be 1
        assert Email.objects.filter(email="existing@example.com").count() == 1

    def test_generate_token_existing_phone(self):
        """Test generating token for existing phone number."""
        # Create existing phone
        existing_phone = PhoneNumber.objects.create(phone_number="+14155551234")

        token = generate_token(phone_number="+14155551234")

        assert token is not None
        assert token.phone_number == existing_phone
        # Phone count should still be 1
        assert PhoneNumber.objects.filter(phone_number="+14155551234").count() == 1

    def test_generate_token_authenticated_user_new_email(self):
        """Test generating token for authenticated user with new email."""
        user = User.objects.create_user(username="testuser", email="test@example.com")  # type: ignore

        token = generate_token(email="new@example.com", user=user)

        assert token is not None
        assert token.email.email == "new@example.com"  # type: ignore
        # Since email is new (created=True), token is saved immediately
        assert AuthToken.objects.filter(token=token.token).exists()

    def test_generate_token_unauthenticated_user(self):
        """Test generating token for unauthenticated user."""
        from django.contrib.auth.models import AnonymousUser

        user = AnonymousUser()
        token = generate_token(email="test@example.com", user=user)

        assert token is not None
        # Token should be saved for anonymous users
        assert AuthToken.objects.filter(token=token.token).exists()

    def test_generate_token_user_email_conflict(self):
        """Test generating token when email belongs to different user."""
        user1 = User.objects.create_user(username="user1", email="user1@example.com")  # type: ignore
        user2 = User.objects.create_user(username="user2", email="user2@example.com")  # type: ignore

        # Create email associated with user1
        Email.objects.create(email="conflict@example.com", user=user1)

        # Try to generate token for user2 with same email
        token = generate_token(email="conflict@example.com", user=user2)

        assert token is None

    def test_generate_token_user_phone_conflict(self):
        """Test generating token when phone belongs to different user."""
        user1 = User.objects.create_user(username="user1", email="user1@example.com")  # type: ignore
        user2 = User.objects.create_user(username="user2", email="user2@example.com")  # type: ignore

        # Create phone associated with user1
        PhoneNumber.objects.create(phone_number="+14155551234", user=user1)

        # Try to generate token for user2 with same phone
        token = generate_token(phone_number="+14155551234", user=user2)

        assert token is None

    def test_generate_token_user_owns_email(self):
        """Test generating token when user owns the email."""
        user = User.objects.create_user(username="testuser", email="test@example.com")  # type: ignore

        # Create email owned by user
        email = Email.objects.create(email="owned@example.com", user=user)

        token = generate_token(email="owned@example.com", user=user)

        assert token is not None
        assert token.email == email
        assert token.email.potential_user == user  # type: ignore

    @patch("stagedoor.models.logger")
    def test_generate_token_logs_error(self, mock_logger):
        """Test that error is logged when no contact info provided."""
        token = generate_token()

        assert token is None
        mock_logger.error.assert_called_once_with(
            "Tried to generate a token for neither email nor sms"
        )
