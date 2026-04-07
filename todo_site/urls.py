from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("dashboard.urls")),
    path("tasks/", include("tasks.urls")),
    path("habits/", include("habits.urls")),
    path("journal/", include("journal.urls")),
]
