# django-stagedoor

Easy email or sms based login for Django

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
