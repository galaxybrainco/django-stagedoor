from django.urls import include, path

urlpatterns = [
    path("auth/", include("stagedoor.urls", namespace="stagedoor")),
]