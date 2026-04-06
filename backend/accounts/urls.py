from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import LoginView, MeView, RegisterView

urlpatterns = [
    path("register", RegisterView.as_view(), name="auth-register"),
    path("login", LoginView.as_view(), name="auth-login"),
    path("token/refresh", TokenRefreshView.as_view(), name="auth-token-refresh"),
]

# /api/me is outside /api/auth/ prefix – added in the root urls alongside accounts
from django.urls import path as _path  # noqa: E402, F811 – re-export for root urls
me_urlpatterns = [
    _path("me", MeView.as_view(), name="auth-me"),
]
