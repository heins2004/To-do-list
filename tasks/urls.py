from django.urls import path

from . import views


urlpatterns = [
    path("create/", views.create_task, name="task_create"),
    path("<int:pk>/toggle/", views.toggle_task, name="task_toggle"),
    path("<int:pk>/delete/", views.delete_task, name="task_delete"),
]
