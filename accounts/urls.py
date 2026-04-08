from django.contrib.auth.views import LogoutView
from django.urls import path

from .views import login_view, register_view, update_profile


urlpatterns = [
    path("login/", login_view, name="login"),
    path("register/", register_view, name="register"),
    path("profile/", update_profile, name="profile_update"),
    path("logout/", LogoutView.as_view(), name="logout"),
]
