from django.urls import path

from . import views


urlpatterns = [
    path("", views.dashboard_home, name="dashboard_home"),
    path("ping/", views.ping, name="ping"),
    path("api/dashboard/", views.dashboard_snapshot, name="dashboard_snapshot"),
]
