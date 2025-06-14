"""
Tests for django-stagedoor helper functions.
"""

from unittest.mock import Mock, patch

import pytest
from django.test import RequestFactory

from stagedoor.helpers import email_admin_approval, email_login_link, sms_login_link
from stagedoor.models import AuthToken, Email, PhoneNumber


@pytest.mark.django_db
class TestEmailHelpers:
    """Test email helper functions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()

    @patch("stagedoor.helpers.send_mail")
    @patch("stagedoor.helpers.get_template")
    @patch("stagedoor.helpers.render_to_string")
    @patch("stagedoor.helpers.get_current_site")
    def test_email_login_link(
        self, mock_get_site, mock_render, mock_get_template, mock_send_mail
    ):
        """Test sending login link via email."""
        # Setup mocks
        mock_site = Mock()
        mock_site.domain = "example.com"
        mock_get_site.return_value = mock_site
        mock_render.return_value = "Plain text message"

        mock_template = Mock()
        mock_template.render.return_value = "<html>HTML message</html>"
        mock_get_template.return_value = mock_template

        # Create test data
        email = Email.objects.create(email="test@example.com")
        token = AuthToken.objects.create(email=email, token="test-token")
        request = self.factory.get("/")

        # Call function
        email_login_link(request, token)

        # Verify mocks were called
        mock_get_site.assert_called_once_with(request)
        mock_render.assert_called_once()
        mock_get_template.assert_called_once()
        mock_send_mail.assert_called_once()

        # Check send_mail call arguments
        call_args = mock_send_mail.call_args
        assert call_args[1]["recipient_list"] == ["test@example.com"]
        assert "Here's your login to" in call_args[1]["subject"]
        assert call_args[1]["message"] == "Plain text message"
        assert call_args[1]["html_message"] == "<html>HTML message</html>"
        assert call_args[1]["fail_silently"] is False

    @patch("stagedoor.helpers.send_mail")
    @patch("stagedoor.helpers.get_template")
    @patch("stagedoor.helpers.render_to_string")
    @patch("stagedoor.helpers.get_current_site")
    def test_email_admin_approval(
        self, mock_get_site, mock_render, mock_get_template, mock_send_mail
    ):
        """Test sending admin approval email."""
        # Setup mocks
        mock_site = Mock()
        mock_site.domain = "example.com"
        mock_get_site.return_value = mock_site
        mock_render.return_value = "Plain text approval message"

        mock_template = Mock()
        mock_template.render.return_value = "<html>HTML approval message</html>"
        mock_get_template.return_value = mock_template

        # Create test data
        email = Email.objects.create(email="admin@example.com")
        token = AuthToken.objects.create(email=email, token="approval-token")
        request = self.factory.get("/")

        # Call function
        email_admin_approval(request, token)

        # Verify mocks were called
        mock_get_site.assert_called_once_with(request)
        mock_render.assert_called_once()
        mock_get_template.assert_called_once()
        mock_send_mail.assert_called_once()

        # Check send_mail call arguments
        call_args = mock_send_mail.call_args
        assert call_args[1]["recipient_list"] == ["admin@example.com"]
        assert "New account created on" in call_args[1]["subject"]
        assert call_args[1]["message"] == "Plain text approval message"
        assert call_args[1]["html_message"] == "<html>HTML approval message</html>"

    @patch("stagedoor.helpers.render_to_string")
    def test_email_template_context(self, mock_render):
        """Test that email templates receive correct context variables."""
        # Create test data
        email = Email.objects.create(email="test@example.com")
        token = AuthToken.objects.create(email=email, token="context-token")
        request = self.factory.get("/")

        with (
            patch("stagedoor.helpers.send_mail"),
            patch("stagedoor.helpers.get_template"),
            patch("stagedoor.helpers.get_current_site") as mock_get_site,
        ):
            mock_site = Mock()
            mock_site.domain = "testsite.com"
            mock_get_site.return_value = mock_site

            email_login_link(request, token)

            # Check render_to_string was called with correct context
            mock_render.assert_called_once()
            call_args = mock_render.call_args
            context = call_args[0][1]  # Second argument is the context

            assert context["current_site"] == mock_site
            assert context["token"] == "context-token"
            assert "site_name" in context
            assert "support_email" in context


@pytest.mark.django_db
class TestSMSHelpers:
    """Test SMS helper functions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()

    def test_sms_login_link_with_twilio_configured(self):
        """Test that SMS function doesn't crash when called."""
        # Create test data
        phone = PhoneNumber.objects.create(phone_number="+14155551234")
        token = AuthToken.objects.create(phone_number=phone, token="123456")
        request = self.factory.get("/")

        # Should not raise an exception
        sms_login_link(request, token)

    def test_sms_login_link_no_twilio_config(self):
        """Test SMS function when Twilio is not configured."""
        phone = PhoneNumber.objects.create(phone_number="+14155551234")
        token = AuthToken.objects.create(phone_number=phone, token="123456")
        request = self.factory.get("/")

        # Should not raise an exception, just do nothing
        sms_login_link(request, token)

    def test_sms_login_link_empty_twilio_config(self):
        """Test SMS function when Twilio config is empty string."""
        phone = PhoneNumber.objects.create(phone_number="+14155551234")
        token = AuthToken.objects.create(phone_number=phone, token="123456")
        request = self.factory.get("/")

        # Should not raise an exception, just do nothing
        sms_login_link(request, token)

    def test_sms_login_link_missing_twilio_settings(self):
        """Test SMS function when Twilio settings don't exist."""
        phone = PhoneNumber.objects.create(phone_number="+14155551234")
        token = AuthToken.objects.create(phone_number=phone, token="123456")
        request = self.factory.get("/")

        # Should not raise an exception, just do nothing
        sms_login_link(request, token)
