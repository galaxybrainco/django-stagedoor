from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.http import HttpRequest
from django.template.loader import get_template, render_to_string

from . import settings as stagedoor_settings
from .models import AuthToken


def email_login_link(request: HttpRequest, token: AuthToken) -> None:
    current_site = get_current_site(request)

    # Send the link by email.
    send_mail(
        subject=f"Here's your login to {stagedoor_settings.SITE_NAME}",
        message=render_to_string(
            stagedoor_settings.EMAIL_TXT_TEMPLATE,
            {
                "current_site": current_site,
                "token": token.token,
                "site_name": stagedoor_settings.SITE_NAME,
                "support_email": stagedoor_settings.SUPPORT_EMAIL,
            },
            request=request,
        ),
        from_email=stagedoor_settings.DEFAULT_FROM_EMAIL,
        recipient_list=[token.email.email],  # type: ignore
        html_message=get_template(stagedoor_settings.EMAIL_HTML_TEMPLATE).render(
            {
                "current_site": current_site,
                "token": token.token,
                "site_name": stagedoor_settings.SITE_NAME,
                "support_email": stagedoor_settings.SUPPORT_EMAIL,
            },
        ),
        fail_silently=False,
    )


def email_admin_approval(request: HttpRequest, token: AuthToken) -> None:
    current_site = get_current_site(request)

    # Determine the contact info for the approval request
    if token.email:
        contact_info = token.email.email
        contact_type = "email"
    elif token.phone_number:
        contact_info = str(token.phone_number.phone_number)
        contact_type = "phone number"
    else:
        contact_info = "unknown"
        contact_type = "contact method"

    # Send the approval request email to support/admin email
    send_mail(
        subject=f"New account created on {stagedoor_settings.SITE_NAME}",
        message=render_to_string(
            stagedoor_settings.APPROVAL_TXT_TEMPLATE,
            {
                "current_site": current_site,
                "token": token.token,
                "site_name": stagedoor_settings.SITE_NAME,
                "support_email": stagedoor_settings.SUPPORT_EMAIL,
                "contact_info": contact_info,
                "contact_type": contact_type,
            },
            request=request,
        ),
        from_email=stagedoor_settings.DEFAULT_FROM_EMAIL,
        recipient_list=[stagedoor_settings.SUPPORT_EMAIL],
        html_message=get_template(stagedoor_settings.APPROVAL_HTML_TEMPLATE).render(
            {
                "current_site": current_site,
                "token": token.token,
                "site_name": stagedoor_settings.SITE_NAME,
                "support_email": stagedoor_settings.SUPPORT_EMAIL,
                "contact_info": contact_info,
                "contact_type": contact_type,
            },
        ),
        fail_silently=False,
    )


def sms_login_link(request: HttpRequest, token: AuthToken) -> None:
    current_site = get_current_site(request)
    if (
        hasattr(settings, "TWILIO_ACCOUNT_SID")
        and hasattr(settings, "TWILIO_AUTH_TOKEN")
        and hasattr(settings, "TWILIO_NUMBER")
        and settings.TWILIO_ACCOUNT_SID is not None
        and settings.TWILIO_AUTH_TOKEN is not None
        and settings.TWILIO_NUMBER is not None
    ):
        from twilio.rest import Client

        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=f"Your {stagedoor_settings.SITE_NAME} code is {token.token}\n\nGo to https://{current_site.domain}/auth/token to login.",  # noqa: E501
            from_=settings.TWILIO_NUMBER,
            to=str(token.phone_number.phone_number),  # type: ignore
        )
