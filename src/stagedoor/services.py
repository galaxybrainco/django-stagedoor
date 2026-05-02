"""
Service layer for django-stagedoor authentication operations.
"""

from typing import TYPE_CHECKING

from django.contrib.auth.models import AbstractBaseUser, AnonymousUser
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from phonenumber_field.validators import validate_international_phonenumber

from .models import AuthToken, generate_token

if TYPE_CHECKING:
    from django.http import HttpRequest


def create_login_token(
    request: "HttpRequest",
    email: str | None = None,
    phone_number: str | None = None,
    next_url: str | None = None,
    user: AbstractBaseUser | AnonymousUser | None = None,
) -> AuthToken | None:
    """Create a login token for the given email or phone number.

    Args:
        request: HTTP request object
        email: Email address to create token for
        phone_number: Phone number to create token for
        next_url: Next URL to redirect to after login
        user: Current authenticated user

    Returns:
        AuthToken object or None if creation fails
    """
    return generate_token(
        email=email,
        phone_number=phone_number,
        next_url=next_url,
        user=user,
    )


def validate_token(token_string: str) -> AuthToken | None:
    """Validate a token string and return the corresponding AuthToken.

    Args:
        token_string: Token string to validate

    Returns:
        AuthToken object if valid, None otherwise
    """
    AuthToken.delete_stale()
    return AuthToken.objects.filter(token=token_string).first()


def validate_contact_info(
    contact_info: str,
) -> tuple[str | None, str | None]:
    """Validate contact information and return email and phone number.

    Args:
        contact_info: Contact information to validate

    Returns:
        Tuple of (email, phone_number) where one may be None
    """
    email = None
    phone_number = None

    try:
        validate_email(contact_info)
        email = contact_info
    except ValidationError:
        try:
            validate_international_phonenumber(contact_info)
            phone_number = contact_info
        except ValidationError:
            pass

    return email, phone_number
