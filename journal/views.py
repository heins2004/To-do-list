import json
from datetime import date

from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST

from .models import DailyNote


@require_POST
def save_daily_note(request):
    body = json.loads(request.body or "{}")
    target_date = date.fromisoformat(body.get("date"))
    content = (body.get("content") or "").rstrip()

    if content:
        note, _ = DailyNote.objects.update_or_create(
            date=target_date,
            defaults={"content": content},
        )
    else:
        DailyNote.objects.filter(date=target_date).delete()
        note = None

    return JsonResponse(
        {
            "ok": True,
            "saved": True,
            "date": target_date.isoformat(),
            "content": note.content if note else "",
        }
    )


@require_GET
def get_daily_note(request, note_date):
    target_date = date.fromisoformat(note_date)
    note = DailyNote.objects.filter(date=target_date).first()
    return JsonResponse(
        {
            "ok": True,
            "date": target_date.isoformat(),
            "content": note.content if note else "",
            "has_note": bool(note and note.content.strip()),
        }
    )
