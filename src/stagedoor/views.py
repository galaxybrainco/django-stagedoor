from urllib.parse import parse_qs, urlparse

from django import forms
from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods
from phonenumber_field.formfields import PhoneNumberField
from phonenumber_field.validators import validate_international_phonenumber

from . import settings as stagedoor_settings
from .helpers import email_admin_approval, email_login_link, sms_login_link
from .models import generate_token


class LoginForm(forms.Form):
    """The form for the login page."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        label = "Your contact information"
        if stagedoor_settings.ENABLE_SMS:
            label = "Your phone number, ie +15555555555"
            self.fields["phone_number"] = PhoneNumberField(
                label="Your phone number", required=False
            )
        if stagedoor_settings.ENABLE_EMAIL:
            label = "Your email"
            self.fields["email"] = forms.EmailField(
                label="Your email address", required=False
            )
        if stagedoor_settings.ENABLE_SMS and stagedoor_settings.ENABLE_EMAIL:
            label = "Your phone number or email"

        self.fields["contact"] = forms.CharField(label=label, required=False)
        self.fields["next"] = forms.CharField(required=False)

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data:
            return self.cleaned_data
        form_email = cleaned_data.get("email")
        form_phone_number = cleaned_data.get("phone_number")

        try:
            contact_email = cleaned_data.get("contact")
            validate_email(contact_email)
        except ValidationError:
            contact_email = None
        try:
            contact_phone = cleaned_data.get("contact")
            validate_international_phonenumber(contact_phone)
        except ValidationError:
            contact_phone = None

        email = contact_email if not form_email else form_email
        phone_number = contact_phone if not form_phone_number else form_phone_number

        if not email and not phone_number:
            raise forms.ValidationError(
                "Please use a valid email address or phone number."
            )

        self.cleaned_data["phone_number"] = phone_number
        self.cleaned_data["email"] = email
        return self.cleaned_data


@require_http_methods(["POST"])
def login_post(request: HttpRequest) -> HttpResponse:
    """Process the submission of the form with the user's email and mail them a link."""
    form = LoginForm(request.POST)
    if not form.is_valid():
        messages.error(
            request,
            _("Please use a valid email address or phone number."),
        )
        return redirect(stagedoor_settings.LOGIN_URL)

    email = form.cleaned_data["email"]
    phone_number = form.cleaned_data["phone_number"]

    next_url: str | None = ""
    if parsed_next_url := parse_qs(urlparse(request.get_full_path()).query).get("next"):
        next_url = parsed_next_url[0]

    if email:
        if token := generate_token(email=email, next_url=next_url, user=request.user):
            # breakpoint()
            if stagedoor_settings.REQUIRE_ADMIN_APPROVAL:
                token.approved = False
                token.save()
                email_admin_approval(request=request, token=token)
                return redirect(reverse("stagedoor:approval-needed"))
            else:
                email_login_link(request=request, token=token)
                messages.success(
                    request,
                    _("Check your email to log in!"),
                )
                return redirect(reverse("stagedoor:token-post"))
        else:
            messages.error(
                request, _("A user with that email already exists.")
            )  # TODO: I think this is the wrong error
            return redirect(stagedoor_settings.LOGIN_URL)

    elif phone_number:
        if token := generate_token(
            phone_number=phone_number, next_url=next_url, user=request.user
        ):
            if stagedoor_settings.REQUIRE_ADMIN_APPROVAL:
                token.approved = False
                token.save()
                email_admin_approval(request=request, token=token)
                return redirect(reverse("stagedoor:admin-approval"))
            else:
                sms_login_link(request=request, token=token)
                messages.success(
                    request,
                    _("Check your text messages to log in!"),
                )
                return redirect(reverse("stagedoor:token-post"))
        else:
            messages.error(request, _("A user with that phone number already exists."))
            return redirect(stagedoor_settings.LOGIN_URL)

    return redirect(stagedoor_settings.LOGIN_URL)


def process_token(request: HttpRequest, token: str | None) -> HttpResponse:
    user = authenticate(request, token=token)
    if user is None:
        messages.error(
            request,
            _(
                "The login link is invalid or has expired, or you are not allowed to "
                "log in. Please try again."
            ),
        )
        return redirect(stagedoor_settings.LOGIN_URL)

    if hasattr(user, "_stagedoor_next_url"):
        next_url = user._stagedoor_next_url  # type: ignore

        # Remove the next URL from the user object.
        del user._stagedoor_next_url  # type: ignore
    else:
        next_url = stagedoor_settings.LOGIN_REDIRECT

    if not request.user.is_authenticated:
        django_login(request, user)
    messages.success(request, _("Login successful."))
    return redirect(next_url)


def token_post(request: HttpRequest) -> HttpResponse:
    if request.POST:
        token = request.POST.get("token")
        return process_token(request, token)
    return render(request, template_name="stagedoor_token_input.html")


@require_http_methods(["GET"])
def token_login(request: HttpRequest, token: str) -> HttpResponse:
    """Validate the token the user submitted."""
    return process_token(request, token)


@login_required  # type: ignore
def logout(request: HttpRequest) -> HttpResponse:
    django_logout(request)
    messages.success(request, _("You have been logged out."))
    return redirect(stagedoor_settings.LOGOUT_REDIRECT)


def approval_needed(request: HttpRequest) -> HttpResponse:
    return render(request, template_name="stagedoor_approval_needed.html")
