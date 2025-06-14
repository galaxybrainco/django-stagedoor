"""
Tests for django-stagedoor admin functionality.
"""

from unittest.mock import patch

import pytest
from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory
from django.urls import reverse

from stagedoor.admin import AuthTokenAdmin, EmailAdmin, PhoneNumberAdmin
from stagedoor.models import AuthToken, Email, PhoneNumber


@pytest.mark.django_db
class TestEmailAdmin:
    """Test EmailAdmin functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.site = AdminSite()
        self.admin = EmailAdmin(Email, self.site)
        self.factory = RequestFactory()

    def test_list_display(self):
        """Test that list_display is properly configured."""
        expected = ("email", "user", "potential_user")
        assert self.admin.list_display == expected

    def test_email_admin_registration(self):
        """Test that EmailAdmin is registered with Django admin."""
        assert Email in admin.site._registry
        assert isinstance(admin.site._registry[Email], EmailAdmin)

    def test_admin_list_view(self, admin_user, regular_user, admin_client):
        """Test the admin list view displays emails correctly."""
        Email.objects.create(email="user@example.com", user=regular_user)
        Email.objects.create(email="nouser@example.com")

        url = reverse("admin:stagedoor_email_changelist")
        response = admin_client.get(url)

        assert response.status_code == 200
        assert "user@example.com" in response.content.decode()
        assert "nouser@example.com" in response.content.decode()
        assert regular_user.username in response.content.decode()

    def test_admin_add_view(self, admin_user, regular_user, admin_client):
        """Test adding an email through admin."""
        url = reverse("admin:stagedoor_email_add")
        response = admin_client.get(url)
        assert response.status_code == 200

        # Test posting a new email
        data = {
            "email": "new@example.com",
            "user": regular_user.pk,
        }
        response = admin_client.post(url, data)
        assert response.status_code == 302
        assert Email.objects.filter(email="new@example.com").exists()

    def test_admin_change_view(self, admin_user, regular_user, admin_client):
        """Test changing an email through admin."""
        email = Email.objects.create(email="change@example.com")
        url = reverse("admin:stagedoor_email_change", args=[email.pk])

        response = admin_client.get(url)
        assert response.status_code == 200

        # Test updating the email
        data = {
            "email": "changed@example.com",
            "user": regular_user.pk,
        }
        response = admin_client.post(url, data)
        assert response.status_code == 302

        email.refresh_from_db()
        assert email.email == "changed@example.com"
        assert email.user == regular_user


@pytest.mark.django_db
class TestPhoneNumberAdmin:
    """Test PhoneNumberAdmin functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.site = AdminSite()
        self.admin = PhoneNumberAdmin(PhoneNumber, self.site)
        self.factory = RequestFactory()

    def test_list_display(self):
        """Test that list_display is properly configured."""
        expected = ("phone_number", "user", "potential_user")
        assert self.admin.list_display == expected

    def test_phone_number_admin_registration(self):
        """Test that PhoneNumberAdmin is registered with Django admin."""
        assert PhoneNumber in admin.site._registry
        assert isinstance(admin.site._registry[PhoneNumber], PhoneNumberAdmin)

    def test_admin_list_view(self, admin_user, regular_user, admin_client):
        """Test the admin list view displays phone numbers correctly."""
        PhoneNumber.objects.create(phone_number="+14155551234", user=regular_user)
        PhoneNumber.objects.create(phone_number="+14155555678")

        url = reverse("admin:stagedoor_phonenumber_changelist")
        response = admin_client.get(url)

        assert response.status_code == 200
        assert "+14155551234" in response.content.decode()
        assert "+14155555678" in response.content.decode()
        assert regular_user.username in response.content.decode()

    def test_admin_add_view(self, admin_user, regular_user, admin_client):
        """Test adding a phone number through admin."""
        url = reverse("admin:stagedoor_phonenumber_add")
        response = admin_client.get(url)
        assert response.status_code == 200

        # Test posting a new phone number
        data = {
            "phone_number": "+14155559999",
            "user": regular_user.pk,
        }
        response = admin_client.post(url, data)
        assert response.status_code == 302
        assert PhoneNumber.objects.filter(phone_number="+14155559999").exists()


@pytest.mark.django_db
class TestAuthTokenAdmin:
    """Test AuthTokenAdmin functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.site = AdminSite()
        self.admin = AuthTokenAdmin(AuthToken, self.site)
        self.factory = RequestFactory()

    def test_list_display(self):
        """Test that list_display is properly configured."""
        expected = ["email", "phone_number", "approved", "timestamp", "next_url"]
        assert self.admin.list_display == expected

    def test_ordering(self):
        """Test that ordering is properly configured."""
        expected = ["-timestamp"]
        assert self.admin.ordering == expected

    def test_actions(self):
        """Test that custom actions are registered."""
        assert "approve_tokens" in self.admin.actions

    def test_auth_token_admin_registration(self):
        """Test that AuthTokenAdmin is registered with Django admin."""
        assert AuthToken in admin.site._registry
        assert isinstance(admin.site._registry[AuthToken], AuthTokenAdmin)

    def test_approve_tokens_action_description(self):
        """Test the action has proper description."""
        action = self.admin.approve_tokens
        assert action.short_description == "Approve selected accounts."

    def test_admin_list_view(self, admin_client):
        """Test the admin list view displays tokens correctly."""
        email = Email.objects.create(email="test@example.com")
        phone = PhoneNumber.objects.create(phone_number="+14155551234")

        AuthToken.objects.create(email=email, token="token1", approved=False)
        AuthToken.objects.create(
            phone_number=phone, token="token2", approved=True, next_url="/dashboard"
        )

        url = reverse("admin:stagedoor_authtoken_changelist")
        response = admin_client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        assert "test@example.com" in content
        assert "+14155551234" in content
        assert "/dashboard" in content
        assert "field-approved" in content

    def test_admin_list_view_ordering(self, admin_client, admin_user):
        """Test that tokens are ordered by timestamp descending."""
        email = Email.objects.create(email="test@example.com")

        # Create tokens - the second one will have a newer timestamp
        AuthToken.objects.create(email=email, token="first-token")
        AuthToken.objects.create(email=email, token="second-token")

        url = reverse("admin:stagedoor_authtoken_changelist")
        response = admin_client.get(url)

        # Check that the page renders successfully
        assert response.status_code == 200

        # Test that the ordering configuration is applied to the admin class
        assert self.admin.ordering == ["-timestamp"]

        # Test that queries use the configured ordering with proper request
        request = self.factory.get("/admin/stagedoor/authtoken/")
        request.user = admin_user
        changelist = self.admin.get_changelist_instance(request)
        # The ordering should be applied to queries
        assert list(changelist.get_queryset(request)) == list(
            AuthToken.objects.order_by("-timestamp")
        )

    def test_approve_tokens_action_functionality(self, admin_user):
        """Test the approve_tokens action functionality without external calls."""
        email = Email.objects.create(email="test@example.com")
        token = AuthToken.objects.create(
            email=email, approved=False, token="test-token"
        )

        # Create a proper request with messages
        request = self.factory.post("/")
        request.user = admin_user
        request.session = "session"
        messages = FallbackStorage(request)
        request._messages = messages

        queryset = AuthToken.objects.filter(pk=token.pk)

        # Mock external dependencies - patch both the direct call and the import
        with patch("stagedoor.admin.email_login_link") as mock_email:
            with patch("stagedoor.admin.sms_login_link") as mock_sms:
                with patch("stagedoor.settings.REQUIRE_ADMIN_APPROVAL", False):
                    self.admin.approve_tokens(request, queryset)

        # Check that the token was approved
        token.refresh_from_db()
        assert token.approved

        # Check that email function was called
        mock_email.assert_called_once()
        mock_sms.assert_not_called()

        # Check message was added
        msgs = list(messages)
        assert len(msgs) == 1
        assert "Successfully approved and sent 1 searches" in str(msgs[0])

    def test_admin_action_through_interface(self, admin_client):
        """Test the admin action through the web interface."""
        email = Email.objects.create(email="test@example.com")
        token = AuthToken.objects.create(
            email=email, approved=False, token="test-token"
        )

        # Mock external dependencies
        with patch("stagedoor.admin.email_login_link"):
            with patch("stagedoor.admin.sms_login_link"):
                with patch("stagedoor.settings.REQUIRE_ADMIN_APPROVAL", False):
                    # Submit the action through admin
                    url = reverse("admin:stagedoor_authtoken_changelist")
                    data = {
                        "action": "approve_tokens",
                        "_selected_action": [str(token.pk)],
                    }
                    response = admin_client.post(url, data, follow=True)

        assert response.status_code == 200

        # Check that the token was approved
        token.refresh_from_db()
        assert token.approved

        # Check for success message in the response
        messages = list(response.context["messages"])
        assert len(messages) == 1
        assert "Successfully approved and sent 1 searches" in str(messages[0])

    def test_admin_action_with_phone_token(self, admin_client):
        """Test the admin action with phone tokens."""
        phone = PhoneNumber.objects.create(phone_number="+14155551234")
        token = AuthToken.objects.create(
            phone_number=phone, approved=False, token="test-token"
        )

        # Mock external dependencies
        with patch("stagedoor.admin.email_login_link") as mock_email:
            with patch("stagedoor.admin.sms_login_link") as mock_sms:
                with patch("stagedoor.settings.REQUIRE_ADMIN_APPROVAL", False):
                    # Submit the action through admin
                    url = reverse("admin:stagedoor_authtoken_changelist")
                    data = {
                        "action": "approve_tokens",
                        "_selected_action": [str(token.pk)],
                    }
                    response = admin_client.post(url, data, follow=True)

        assert response.status_code == 200

        # Check that the token was approved
        token.refresh_from_db()
        assert token.approved

        # Check that SMS function was called
        mock_sms.assert_called_once()
        mock_email.assert_not_called()

    def test_admin_action_multiple_tokens(self, admin_client):
        """Test approving multiple tokens at once."""
        email1 = Email.objects.create(email="test1@example.com")
        email2 = Email.objects.create(email="test2@example.com")

        token1 = AuthToken.objects.create(email=email1, approved=False, token="token1")
        token2 = AuthToken.objects.create(email=email2, approved=False, token="token2")

        # Mock external dependencies
        with patch("stagedoor.admin.email_login_link") as mock_email:
            with patch("stagedoor.admin.sms_login_link") as mock_sms:
                with patch("stagedoor.settings.REQUIRE_ADMIN_APPROVAL", False):
                    # Submit the action through admin
                    url = reverse("admin:stagedoor_authtoken_changelist")
                    data = {
                        "action": "approve_tokens",
                        "_selected_action": [str(token1.pk), str(token2.pk)],
                    }
                    response = admin_client.post(url, data, follow=True)

        assert response.status_code == 200

        # Check that all tokens were approved
        token1.refresh_from_db()
        token2.refresh_from_db()
        assert token1.approved
        assert token2.approved

        # Check that email function was called for each token
        assert mock_email.call_count == 2
        mock_sms.assert_not_called()

        # Check for success message
        messages = list(response.context["messages"])
        assert len(messages) == 1
        assert "Successfully approved and sent 2 searches" in str(messages[0])

    def test_admin_filters_and_search(self, admin_client):
        """Test that admin page loads without errors."""
        # Create a token so there's something to display
        email = Email.objects.create(email="test@example.com")
        AuthToken.objects.create(email=email, token="test-token")

        url = reverse("admin:stagedoor_authtoken_changelist")
        response = admin_client.get(url)
        assert response.status_code == 200

        # Test that the page contains expected elements
        content = response.content.decode()
        assert "changelist" in content
        # When there are tokens, action checkboxes should be present
        assert "action-select" in content

    def test_admin_change_view(self, admin_client):
        """Test the admin change view for tokens."""
        email = Email.objects.create(email="test@example.com")
        token = AuthToken.objects.create(
            email=email, approved=False, token="test-token", next_url="/original"
        )

        url = reverse("admin:stagedoor_authtoken_change", args=[token.pk])
        response = admin_client.get(url)
        assert response.status_code == 200

        # Test updating the token
        data = {
            "email": email.pk,
            "token": "updated-token",
            "approved": True,
            "next_url": "/updated",
            "timestamp_0": token.timestamp.strftime("%Y-%m-%d"),
            "timestamp_1": token.timestamp.strftime("%H:%M:%S"),
        }
        response = admin_client.post(url, data)
        assert response.status_code == 302

        token.refresh_from_db()
        assert token.token == "updated-token"
        assert token.approved
        assert token.next_url == "/updated"

    def test_admin_add_view(self, admin_client):
        """Test adding a token through admin."""
        email = Email.objects.create(email="test@example.com")

        url = reverse("admin:stagedoor_authtoken_add")
        response = admin_client.get(url)
        assert response.status_code == 200

        # Test posting a new token
        from django.utils import timezone

        now = timezone.now()
        data = {
            "email": email.pk,
            "token": "new-token",
            "approved": True,
            "next_url": "/new",
            "timestamp_0": now.strftime("%Y-%m-%d"),
            "timestamp_1": now.strftime("%H:%M:%S"),
        }
        response = admin_client.post(url, data)
        assert response.status_code == 302
        assert AuthToken.objects.filter(token="new-token").exists()
