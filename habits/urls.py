from django.urls import path

from . import views


urlpatterns = [
    path("create/", views.create_habit, name="habit_create"),
    path("<int:pk>/toggle/", views.toggle_habit, name="habit_toggle"),
    path("<int:pk>/delete/", views.delete_habit, name="habit_delete"),
]
