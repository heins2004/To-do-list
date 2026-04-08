from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from dashboard.services import build_dashboard_payload, ensure_achievements, update_achievements

from .forms import TaskForm
from .models import Task


@login_required
@require_POST
def create_task(request):
    form = TaskForm(request.POST)
    if not form.is_valid():
        return JsonResponse({"ok": False, "errors": form.errors}, status=400)

    task = form.save(commit=False)
    task.owner = request.user
    task.save()
    ensure_achievements(request.user)
    payload = build_dashboard_payload(request.user, selected_date=task.due_date)
    return JsonResponse({"ok": True, "message": "Quest added.", "payload": payload})


@login_required
@require_POST
def toggle_task(request, pk):
    task = get_object_or_404(Task, pk=pk, owner=request.user)
    task.completed = not task.completed
    task.save(update_fields=["completed", "updated_at"])
    update_achievements(user=request.user)
    payload = build_dashboard_payload(request.user, selected_date=task.due_date)
    return JsonResponse({"ok": True, "completed": task.completed, "payload": payload})


@login_required
@require_POST
def delete_task(request, pk):
    task = get_object_or_404(Task, pk=pk, owner=request.user)
    target_date = task.due_date
    task.delete()
    payload = build_dashboard_payload(
        request.user,
        selected_date=target_date if target_date >= timezone.localdate().replace(day=1) else timezone.localdate(),
    )
    return JsonResponse({"ok": True, "message": "Quest deleted.", "payload": payload})
