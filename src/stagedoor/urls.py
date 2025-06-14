from django.urls import path

from . import views

app_name = "stagedoor"
urlpatterns = [
    path("login", views.login_post, name="login"),  # type: ignore
    path("login/<str:token>", views.token_login, name="token-login"),  # type: ignore
    path("logout", views.logout, name="logout"),  # type: ignore
    path("token", views.token_post, name="token-post"),  # type: ignore
    path("approval-needed", views.approval_needed, name="approval-needed"),  # type: ignore
]
