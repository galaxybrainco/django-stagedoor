from django.contrib import admin

from .models import AuthToken, Email, PhoneNumber


@admin.register(Email)
class EmailAdmin(admin.ModelAdmin):
    list_display = ("email", "user", "potential_user")


@admin.register(PhoneNumber)
class PhoneNumberAdmin(admin.ModelAdmin):
    list_display = ("phone_number", "user", "potential_user")


@admin.register(AuthToken)
class AuthTokenAdmin(admin.ModelAdmin):
    list_display = ["email", "phone_number", "timestamp", "next_url"]
    ordering = ["-timestamp"]
