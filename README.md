# django-stagedoor

Easy email or SMS based login for Django

## Installation

1. Add `stagedoor` to `INSTALLED_APPS`

   ```python
   INSTALLED_APPS = [
       "django.contrib.admin",
       "django.contrib.auth",
       "django.contrib.contenttypes",
       "django.contrib.sessions",
       "django.contrib.messages",
       "django.contrib.staticfiles",
       "django.contrib.sites",
       "stagedoor",
       ...
   ]
   ```

2. Add the authentication backends. Make sure to keep `ModelBackend` for the admin login

   ```python
   AUTHENTICATION_BACKENDS = (
       "stagedoor.backends.EmailTokenBackend",
       "stagedoor.backends.SMSTokenBackend",
       "django.contrib.auth.backends.ModelBackend",
   )
   ```

3. Add urls

   ```python
   urlpatterns = [
       path("admin/", admin.site.urls),
       path("auth/", include("stagedoor.urls", namespace="stagedoor")),
      ...
   ]
   ```

## Features

- Email-based login with token links
- SMS-based login with one-time codes (via Twilio)
- Admin approval workflow (optional)
- Single-use token support
- Customizable templates and styling
- Support for Django 5.2+
- Management command to clean up stale tokens (`python manage.py cleanup_stale_tokens`)

## Configuration

See `stagedoor/settings.py` for available configuration options.

## Security Considerations

- Tokens expire after a configurable duration (default: 30 minutes)
- Rate limiting available (via optional django-ratelimit)
- Tokens are generated using cryptographically secure randomness
- Email and SMS delivery should be verified for security

## Usage Examples

### Cleanup stale tokens

```bash
python manage.py cleanup_stale_tokens
```

### Basic usage

In your views:

```python
from stagedoor.services import create_login_token

def login_view(request):
    # Create a token for user
    token = create_login_token(request, email="user@example.com")

    # Send the token via email
    # ... email sending logic here

    return redirect("token_post_page")
```
