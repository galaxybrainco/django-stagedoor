from django.contrib import admin

from stagedoor.helpers import email_login_link, sms_login_link

from .models import AuthToken, Email, PhoneNumber


@admin.register(Email)
class EmailAdmin(admin.ModelAdmin):
    list_display = ("email", "user", "potential_user")


@admin.register(PhoneNumber)
class PhoneNumberAdmin(admin.ModelAdmin):
    list_display = ("phone_number", "user", "potential_user")


@admin.register(AuthToken)
class AuthTokenAdmin(admin.ModelAdmin):
    list_display = ["email", "phone_number", "approved", "timestamp", "next_url"]
    ordering = ["-timestamp"]
    actions = ["approve_tokens"]

    @admin.action(description="Approve selected accounts.")
    def approve_tokens(self, request, queryset):
        """Admin action to approve selected accounts."""
        approved_count = 0

        for token in queryset:
            token.approved = True
            token.save()
            if token.email:
                email_login_link(request=request, token=token)
            if token.phone_number:
                sms_login_link(request=request, token=token)
            approved_count += 1

        self.message_user(
            request, f"Successfully approved and sent {approved_count} searches."
        )
