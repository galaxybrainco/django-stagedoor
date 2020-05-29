from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.template.loader import get_template, render_to_string
from django.conf import settings
from . import settings as stagedoor_settings
from .models import AuthToken, Email, PhoneNumber, generate_token_string


def email_login_link(request, token):
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
        recipient_list=[token.email.email],
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


def sms_login_link(request, token):
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
        message = client.messages.create(
            body=f"Your {stagedoor_settings.SITE_NAME} code is {token.token}\n\nGo to https://{current_site.domain}/auth/token to login.",
            from_=settings.TWILIO_NUMBER,
            to=str(token.phone_number.phone_number),
        )
