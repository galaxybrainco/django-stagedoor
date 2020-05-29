from django.contrib.auth import get_user_model

from . import settings as stagedoor_settings
from .models import AuthToken
from .models import generate_token_string


class StageDoorBackendMixin(object):
    def get_user(self, user_id):
        """Get a user by their primary key."""
        User = get_user_model()
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

    def authenticate(self, request, token=None):
        """Authenticate a user given a token"""
        AuthToken.delete_stale()

        token = AuthToken.objects.filter(token=token).first()
        if not token:
            return

        if stagedoor_settings.SINGLE_USE_LINK:
            token.delete()

        User = get_user_model()

        user_args = {}

        if "username" in [
            field.name for field in User._meta.get_fields(include_hidden=True)
        ]:
            user_args["username"] = f"u{generate_token_string()[:8]}"

        user, created = User.objects.get_or_create(**user_args)

        if token.next_url:
            user._stagedoor_next_url = token.next_url

        return user


class EmailTokenBackend(StageDoorBackendMixin):
    def authenticate(self, request, token=None):
        token = AuthToken.objects.filter(token=token, email__isnull=False).first()
        if not token:
            return

        email = token.email
        if (
            email.potential_user
            and request.user.is_authenticated
            and request.user == email.potential_user
        ):
            email.user = email.potential_user
            email.potential_user = None
            email.save()

        if email.user:
            user = email.user
        else:
            user = super(EmailTokenBackend, self).authenticate(request, token.token)

        if user:
            if token.next_url:
                user._stagedoor_next_url = token.next_url
            User = get_user_model()

            if "email" in [
                field.name for field in User._meta.get_fields(include_hidden=True)
            ]:
                user.email = email.email
            if email:
                email.user = user
                email.save()
            if stagedoor_settings.SINGLE_USE_LINK:
                token.delete()
            user.save()
        return user


class SMSTokenBackend(StageDoorBackendMixin):
    def authenticate(self, request, token=None):
        """Authenticate a user given a signed token from email."""
        token = AuthToken.objects.filter(
            token=token, phone_number__isnull=False
        ).first()
        if not token:
            return

        phone_number = token.phone_number

        if (
            phone_number.potential_user
            and request.user.is_authenticated
            and phone_number.potential_user == request.user
        ):
            phone_number.user = phone_number.potential_user
            phone_number.potential_user = None
            phone_number.save()

        if phone_number.user:
            user = phone_number.user
        else:
            user = super(SMSTokenBackend, self).authenticate(request, token.token)

        if user:
            if token.next_url:
                user._stagedoor_next_url = token.next_url
            User = get_user_model()

            if "phone_number" in [
                field.name for field in User._meta.get_fields(include_hidden=True)
            ]:
                user.phone_number = phone_number.phone_number
                user.save()

            if phone_number:
                phone_number.user = user
                phone_number.save()
            if stagedoor_settings.SINGLE_USE_LINK:
                token.delete()
            user.save()
        return user
