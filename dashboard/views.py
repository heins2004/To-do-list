from datetime import date

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET

from .services import build_dashboard_payload, payload_json


def dashboard_home(request):
    payload = build_dashboard_payload()
    return render(
        request,
        "dashboard/index.html",
        {
            "payload": payload,
            "payload_json": payload_json(payload),
        },
    )


@require_GET
def dashboard_snapshot(request):
    selected_date_raw = request.GET.get("date")
    selected_date = date.fromisoformat(selected_date_raw) if selected_date_raw else None
    return JsonResponse({"ok": True, "payload": build_dashboard_payload(selected_date=selected_date)})
