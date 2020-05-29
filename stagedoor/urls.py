from django.urls import path

from . import views


app_name = "stagedoor"
urlpatterns = [
    path("login", views.login_post, name="login"),
    path("login/<str:token>", views.token_login, name="token-login"),
    path("logout", views.logout, name="logout"),
    path("token", views.token_post, name="token-post"),
]
