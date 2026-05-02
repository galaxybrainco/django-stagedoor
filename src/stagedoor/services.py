"""
Service layer for django-stagedoor authentication operations.
"""

from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser, AnonymousUser
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils import timezone
from phonenumber_field.validators import validate_international_phonenumber

from . import settings as stagedoor_settings
from .models import AuthToken, Email, PhoneNumber, generate_token, generate_token_string

if TYPE_CHECKING:
    from django.http import HttpRequest

    User = AbstractBaseUser | AnonymousUser


def create_login_token(
    request: "HttpRequest",
    email: str | None = None,
    phone_number: str | None = None,
    next_url: str | None = None,
    user: "User" | None = None,
) -> AuthToken | None:
    """
    Create a login token for the given email or phone number.
    
    Args:
        request: HTTP request object
        email: Email address to create token for
        phone_number: Phone number to create token for  
        next_url: Next URL to redirect to after login
        user: Current authenticated user
        
    Returns:
        AuthToken object or None if creation fails
    """
    return generate_token(email=email, phone_number=phone_number, next_url=next_url, user=user)


def validate_token(token_string: str) -> AuthToken | None:
    """
    Validate a token string and return the corresponding AuthToken.
    
    Args:
        token_string: Token string to validate
        
    Returns:
        AuthToken object if valid, None otherwise
    """
    # Delete stale tokens
    AuthToken.delete_stale()
    
    return AuthToken.objects.filter(token=token_string).first()


def validate_contact_info(contact_info: str) -> tuple[str | None, str | None]:
    """
    Validate contact information and return email and phone number.
    
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


def get_or_create_user_from_token(token: AuthToken, user: "User" | None = None) -> "User" | None:
    """
    Get or create a user based on a token.
    
    Args:
        token: AuthToken object
        user: Optional existing user
        
    Returns:
        User object or None if creation fails
    """
    User = get_user_model()
    
    # Check if token is already approved or approval not required
    if not stagedoor_settings.REQUIRE_ADMIN_APPROVAL or token.approved:
        # Proceed with user creation/authentication
        pass
    
    # This function would typically be implemented in the backend classes
    # For now, returning None to indicate we'll handle in backends
    return None