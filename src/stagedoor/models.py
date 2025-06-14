import logging
from datetime import timedelta
from random import SystemRandom

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, AnonymousUser
from django.db import models
from django.utils.timezone import now
from phonenumber_field.modelfields import PhoneNumberField

from . import settings as stagedoor_settings

logger = logging.getLogger(__name__)

# mypy: disable-error-code="var-annotated"


class Email(models.Model):
    email = models.EmailField(unique=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="stagedoor_user_email",
    )
    potential_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="stagedoor_potential_user_email",
    )

    def __str__(self) -> str:
        return f"{self.email}: {self.user} (Maybe: {self.potential_user})"


class PhoneNumber(models.Model):
    phone_number = PhoneNumberField(
        help_text="Must include international prefix - e.g. +1 555 555 55555",
        unique=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="stagedoor_user_phone_number",
    )
    potential_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="stagedoor_potential_user_phone_number",
    )

    def __str__(self) -> str:
        return f"{self.phone_number}: {self.user} (Maybe: {self.potential_user})"


class AuthToken(models.Model):
    token = models.CharField(max_length=200, db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    email = models.ForeignKey(Email, blank=True, null=True, on_delete=models.CASCADE)
    phone_number = models.ForeignKey(
        PhoneNumber, blank=True, null=True, on_delete=models.CASCADE
    )
    next_url = models.CharField(max_length=2000, blank=True)
    approved = models.BooleanField(default=True)

    @classmethod
    def delete_stale(cls) -> None:
        """Delete stale tokens; tokens that are more than TOKEN_DURATION seconds old"""
        cls.objects.filter(
            timestamp__lt=now() - timedelta(seconds=stagedoor_settings.TOKEN_DURATION)
        ).delete()

    def __str__(self) -> str:
        return self.timestamp.strftime("%Y-%m-%d %H:%M:%S")  # type: ignore


def generate_token_string(sms: bool = False) -> str:
    token_length = stagedoor_settings.EMAIL_TOKEN_LENGTH
    charset = "abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ123456789"

    if sms:
        charset = "123456789"
        token_length = stagedoor_settings.SMS_TOKEN_LENGTH

    return "".join([SystemRandom().choice(charset) for _ in range(token_length)])


def generate_token(
    email: str | None = None,
    phone_number: str | None = None,
    next_url: str | None = None,
    user: AbstractBaseUser | AnonymousUser | None = None,
) -> AuthToken | None:
    created = False
    object: Email | PhoneNumber | None = None
    email_object: Email | None = None
    phone_number_object: PhoneNumber | None = None
    token_string = ""
    if email:
        token_string = generate_token_string()
        email_object, created = Email.objects.get_or_create(email=email)
        object = email_object
    if phone_number:
        token_string = generate_token_string(sms=True)
        phone_number_object, created = PhoneNumber.objects.get_or_create(
            phone_number=phone_number,
        )
        object = phone_number_object
    if not object:
        logger.error("Tried to generate a token for neither email nor sms")
        return None

    token = AuthToken(
        token=token_string,
        email=email_object,
        phone_number=phone_number_object,
        next_url=next_url or "",
    )

    if (not user or not user.is_authenticated) or created:
        token.save()
        return token
    if object.user and object.user != user:
        return None
    else:
        if isinstance(user, AbstractBaseUser):
            object.potential_user = user
            object.save()
        return token
