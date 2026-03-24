from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from .forms import TaskForm
from .models import Task


def task_list(request):
    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Task added successfully.")
            return redirect("task_list")
    else:
        form = TaskForm()

    tasks = Task.objects.all()
    return render(
        request,
        "tasks/task_list.html",
        {
            "form": form,
            "tasks": tasks,
        },
    )


def task_update(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if request.method == "POST":
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, "Task updated successfully.")
            return redirect("task_list")
    else:
        form = TaskForm(instance=task)

    return render(
        request,
        "tasks/task_form.html",
        {
            "form": form,
            "task": task,
            "page_title": "Edit Task",
            "button_label": "Update Task",
        },
    )


def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if request.method == "POST":
        task.delete()
        messages.success(request, "Task deleted successfully.")
        return redirect("task_list")

    return render(request, "tasks/task_confirm_delete.html", {"task": task})


def task_toggle_status(request, pk):
    task = get_object_or_404(Task, pk=pk)
    task.status = (
        Task.STATUS_COMPLETED
        if task.status == Task.STATUS_PENDING
        else Task.STATUS_PENDING
    )
    task.save(update_fields=["status", "updated_at"])
    messages.success(request, "Task status updated.")
    return redirect("task_list")
