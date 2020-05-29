from django.conf import settings


TOKEN_DURATION = getattr(settings, "STAGEDOOR_TOKEN_DURATION", 30 * 60)

EMAIL_TOKEN_LENGTH = getattr(settings, "STAGEDOOR_EMAIL_TOKEN_LENGTH", 8)

SMS_TOKEN_LENGTH = getattr(settings, "STAGEDOOR_SMS_TOKEN_LENGTH", 6)

LOGIN_URL = getattr(settings, "STAGEDOOR_LOGIN_URL", settings.LOGIN_URL)

LOGIN_REDIRECT = getattr(
    settings, "STAGEDOOR_LOGIN_REDIRECT", settings.LOGIN_REDIRECT_URL
)
LOGOUT_REDIRECT = getattr(
    settings,
    "STAGEDOOR_LOGOUT_REDIRECT",
    settings.LOGOUT_REDIRECT_URL or settings.LOGIN_REDIRECT_URL,
)

DEFAULT_FROM_EMAIL = getattr(
    settings, "STAGEDOOR_DEFAULT_FROM_EMAIL", settings.DEFAULT_FROM_EMAIL
)

SUPPORT_EMAIL = getattr(
    settings, "STAGEDOOR_SUPPORT_EMAIL", settings.DEFAULT_FROM_EMAIL
)

SINGLE_USE_LINK = getattr(settings, "STAGEDOOR_SINGLE_USE_LINK", False)

EMAIL_HTML_TEMPLATE = getattr(
    settings, "STAGEDOOR_EMAIL_HTML_TEMPLATE", "stagedoor_email.html"
)
EMAIL_TXT_TEMPLATE = getattr(
    settings, "STAGEDOOR_EMAIL_TXT_TEMPLATE", "stagedoor_email.txt"
)

ALLOW_MULTIPLE_EMAILS = getattr(settings, "STAGEDOOR_ALLOW_MULTIPLE_EMAILS", False)

ALLOW_MULTIPLE_PHONE_NUMBERS = getattr(
    settings, "STAGEDOOR_ALLOW_MULTIPLE_PHONE_NUMBERS", False
)

ENABLE_SMS = getattr(settings, "STAGEDOOR_ENABLE_SMS_OVERRIDE", False) or (
    hasattr(settings, "TWILIO_ACCOUNT_SID")
    and hasattr(settings, "TWILIO_AUTH_TOKEN")
    and hasattr(settings, "TWILIO_NUMBER")
)

ENABLE_EMAIL = getattr(settings, "STAGEDOOR_ENABLE_EMAIL_OVERRIDE", False) or (
    hasattr(settings, "EMAIL_HOST")
    and hasattr(settings, "EMAIL_HOST_USER")
    and hasattr(settings, "EMAIL_HOST_PASSWORD")
)

SITE_NAME = getattr(settings, "STAGEDOOR_SITE_NAME", "Django")
