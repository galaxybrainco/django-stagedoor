import logging
import random
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import models
from django.utils.timezone import now

from django.conf import settings

from phonenumber_field.modelfields import PhoneNumberField

from . import settings as stagedoor_settings

logger = logging.getLogger(__name__)


def generate_token_string(email=False, sms=False):
    if email and sms:
        logger.error("Tried to generate a token for email and sms")
        return
    token_length = stagedoor_settings.EMAIL_TOKEN_LENGTH
    charset = "abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ123456789"

    if sms:
        charset = "123456789"
        token_length = stagedoor_settings.SMS_TOKEN_LENGTH

    return "".join([random.choice(charset) for _ in range(token_length)])


def generate_sms_token(phone_number, next_url, user=None):
    token_string = generate_token_string(sms=True)
    phone_number, created = PhoneNumber.objects.get_or_create(
        phone_number=phone_number,
    )
    if (not user or not user.is_authenticated) or created:
        token = AuthToken.objects.create(
            token=token_string, phone_number=phone_number, next_url=next_url,
        )
        return token
    else:
        if phone_number.user and phone_number.user != user:
            return None
        else:
            phone_number.potential_user = user
            phone_number.save()
            token = AuthToken.objects.create(
                token=token_string, phone_number=phone_number, next_url=redirect_url,
            )
            return token


def generate_email_token(email, next_url, user=None):
    token_string = generate_token_string(email=True)
    email, created = Email.objects.get_or_create(email=email)
    if (not user or not user.is_authenticated) or created:
        token = AuthToken.objects.create(
            token=token_string, email=email, next_url=next_url
        )
        return token

    if email.user and email.user != user:
        return None
    else:
        email.potential_user = user
        email.save()
        token = AuthToken.objects.create(
            token=token_string, email=email, next_url=redirect_url
        )
        return token


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

    def __str__(self):
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

    def __str__(self):
        return f"{self.phone_number}: {self.user} (Maybe: {self.potential_user})"


class AuthToken(models.Model):
    token = models.CharField(max_length=200, db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    email = models.ForeignKey(Email, blank=True, null=True, on_delete=models.CASCADE)
    phone_number = models.ForeignKey(
        PhoneNumber, blank=True, null=True, on_delete=models.CASCADE
    )
    next_url = models.CharField(max_length=2000, blank=True)

    @classmethod
    def delete_stale(cls):
        """Delete stale tokens, ie tokens that are more than TOKEN_DURATION seconds older."""
        cls.objects.filter(
            timestamp__lt=now() - timedelta(seconds=stagedoor_settings.TOKEN_DURATION)
        ).delete()

    def __str__(self):
        return self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
