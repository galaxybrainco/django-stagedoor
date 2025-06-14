"""
Pytest configuration for django-stagedoor tests.
"""

import django
import pytest
from django.conf import settings


def pytest_configure():
    """Configure Django settings for tests."""
    if not settings.configured:
        django.setup()


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """
    Enable database access for all tests.
    This fixture is automatically used for all tests.
    """
    pass


@pytest.fixture
def admin_user(django_user_model):
    """Create a superuser for admin tests."""
    return django_user_model.objects.create_superuser(
        username="admin", email="admin@example.com", password="adminpass"
    )


@pytest.fixture
def regular_user(django_user_model):
    """Create a regular user for tests."""
    return django_user_model.objects.create_user(
        username="testuser", email="test@example.com", password="testpass"
    )
