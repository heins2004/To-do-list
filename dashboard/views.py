from datetime import date

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_GET

from .services import build_dashboard_payload, payload_json


@require_GET
def ping(request):
    return JsonResponse({"ok": True, "status": "alive", "timestamp": timezone.now().isoformat()})


@login_required
def dashboard_home(request):
    payload = build_dashboard_payload(request.user)
    return render(
        request,
        "dashboard/index.html",
        {
            "payload": payload,
            "payload_json": payload_json(payload),
        },
    )


@login_required
@require_GET
def dashboard_snapshot(request):
    selected_date_raw = request.GET.get("date")
    selected_date = date.fromisoformat(selected_date_raw) if selected_date_raw else None
    return JsonResponse({"ok": True, "payload": build_dashboard_payload(request.user, selected_date=selected_date)})
