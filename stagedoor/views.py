from django import forms
from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods

from phonenumber_field.formfields import PhoneNumberField

from django.core.validators import validate_email
from django.core.validators import ValidationError

from phonenumber_field.validators import validate_international_phonenumber

from . import settings as stagedoor_settings
from .helpers import email_login_link, sms_login_link
from .models import (
    AuthToken,
    Email,
    PhoneNumber,
    generate_email_token,
    generate_sms_token,
    generate_token_string,
)


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

        self.fields["contact"] = contact = forms.CharField(label=label, required=False)

    def clean(self):
        cleaned_data = super().clean()
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
def login_post(request):
    """Process the submission of the form with the user's email and mail them a link."""
    form = LoginForm(request.POST)
    if not form.is_valid():
        messages.error(
            request, _("Please use a valid email address or phone number."),
        )
        return redirect(stagedoor_settings.LOGIN_URL)

    email = form.cleaned_data["email"]
    phone_number = form.cleaned_data["phone_number"]

    redirect_url = ""
    if request.GET and request.GET.get("next"):
        redirect_url = request.GET.get("next", "")

    if email:
        token = generate_email_token(email, next_url=redirect_url, user=request.user)
        if token:
            email_login_link(request=request, token=token)
            messages.success(
                request, _("Check your email to log in!"),
            )
            return redirect(reverse("stagedoor:token-post"))
        else:
            messages.error(request, _("A user with that email already exists."))
            return redirect(stagedoor_settings.LOGIN_URL)

    elif phone_number:
        token = generate_sms_token(
            phone_number, next_url=redirect_url, user=request.user
        )
        if token:
            sms_login_link(request=request, token=token)
            messages.success(
                request, _("Check your text messages to log in!"),
            )
            return redirect(reverse("stagedoor:token-post"))
        else:
            messages.error(request, _("A user with that phone number already exists."))
            return redirect(stagedoor_settings.LOGIN_URL)

    return redirect(stagedoor_settings.LOGIN_URL)


def process_token(request, token):
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
        # Get the next URL from the user object, if it was set by our custom `authenticate`.
        next_url = user._stagedoor_next_url

        # Remove the next URL from the user object.
        del user._stagedoor_next_url
    else:
        next_url = stagedoor_settings.LOGIN_REDIRECT

    if not request.user.is_authenticated:
        django_login(request, user)
    messages.success(request, _("Login successful."))
    return redirect(next_url)


def token_post(request):
    if request.POST:
        token = request.POST.get("token")
        return process_token(request, token)
    return render(request, template_name="stagedoor_token_input.html")


@require_http_methods(["GET"])
def token_login(request, token):
    """Validate the token the user submitted."""
    return process_token(request, token)


@login_required
def logout(request):
    django_logout(request)
    messages.success(request, _("You have been logged out."))
    return redirect(stagedoor_settings.LOGOUT_REDIRECT)
