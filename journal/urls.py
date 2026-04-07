from django.urls import path

from . import views


urlpatterns = [
    path("save/", views.save_daily_note, name="journal_save"),
    path("<str:note_date>/", views.get_daily_note, name="journal_get"),
]
