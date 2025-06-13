from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import AbstractUser

from . import settings as stagedoor_settings
from .models import AuthToken, Email, generate_token_string


class StageDoorBackend(BaseBackend):
    def get_user(self, user_id: int | str) -> AbstractUser | None:
        """Get a user by their primary key."""
        User = get_user_model()
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

    def get_token_object(self, token: str | int) -> AuthToken | None:
        """Get token object by token string."""
        AuthToken.delete_stale()
        return AuthToken.objects.filter(token=token).first()

    def authenticate(
        self, request, token: str | int | None = None
    ) -> AbstractUser | None:
        """Authenticate a user given a token"""
        user = None
        AuthToken.delete_stale()

        token_object: AuthToken | None = AuthToken.objects.filter(token=token).first()
        if not token_object:
            return None

        if stagedoor_settings.SINGLE_USE_LINK:
            token_object.delete()

        User = get_user_model()

        user_args = {}

        if token_object.email and token_object.email.user:
            user = token_object.email.user
        if token_object.phone_number and token_object.phone_number.user:
            user = token_object.phone_number.user

        if not user and not stagedoor_settings.DISABLE_USER_CREATION:
            if "username" in [
                field.name for field in User._meta.get_fields(include_hidden=True)
            ]:
                user_args["username"] = f"u{generate_token_string()[:8]}"

            user, _ = User.objects.get_or_create(**user_args)

        if token_object.next_url:
            user._stagedoor_next_url = token_object.next_url  # type: ignore

        return user


class EmailTokenBackend(StageDoorBackend):
    def authenticate(
        self, request, token: str | int | None = None
    ) -> AbstractUser | None:
        if not token:
            return None
        token_object = self.get_token_object(token)
        if not token_object:
            return None
        user = super().authenticate(request, token=token_object.token)
        if not user:
            return None

        email: Email | None = token_object.email
        if not email:
            # Something has gone _real_ weird, let's be safe and return None
            return None
        if email.potential_user and email.potential_user != user:
            # Something has gone _real_ weird, let's be safe and return None
            return None

        email.user = user
        email.potential_user = None

        User = get_user_model()
        if "email" in [
            field.name for field in User._meta.get_fields(include_hidden=True)
        ]:
            user.email = email.email
        if stagedoor_settings.SINGLE_USE_LINK:
            token_object.delete()
        user.save()
        email.save()
        return user


class SMSTokenBackend(StageDoorBackend):
    def authenticate(
        self, request, token: str | int | None = None
    ) -> AbstractUser | None:
        if not token:
            return None
        token_object = self.get_token_object(token)
        if not token_object:
            return None
        user = super().authenticate(request, token=token_object.token)
        if not user:
            return None

        phone_number = token_object.phone_number
        if not phone_number:
            # Something has gone _real_ weird, let's be safe and return None
            return None
        if phone_number.potential_user and phone_number.potential_user != user:
            # Something has gone _real_ weird, let's be safe and return None
            return None

        phone_number.user = user
        phone_number.potential_user = None

        User = get_user_model()
        if "phone_number" in [
            field.name for field in User._meta.get_fields(include_hidden=True)
        ]:
            user.phone_number = phone_number.phone_number  # type: ignore
        if stagedoor_settings.SINGLE_USE_LINK:
            token_object.delete()
        user.save()
        phone_number.save()
        return user
