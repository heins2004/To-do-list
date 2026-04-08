from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST

from dashboard.services import build_dashboard_payload, payload_json

from .forms import ProfileUpdateForm, RegisterForm, StyledAuthenticationForm


class DoMatrixLoginView(LoginView):
    authentication_form = StyledAuthenticationForm
    template_name = "accounts/login.html"
    redirect_authenticated_user = True


def login_view(request):
    return DoMatrixLoginView.as_view()(request)


def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard_home")

    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect(reverse_lazy("dashboard_home"))

    return render(request, "accounts/register.html", {"form": form})


@login_required
@require_POST
def update_profile(request):
    form = ProfileUpdateForm(request.POST, instance=request.user)
    if not form.is_valid():
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"ok": False, "errors": form.errors}, status=400)
        payload = build_dashboard_payload(request.user)
        return render(
            request,
            "dashboard/index.html",
            {
                "payload": payload,
                "payload_json": payload_json(payload),
                "profile_form_errors": form.errors,
                "open_profile_form": True,
            },
            status=400,
        )

    user = form.save()
    if form.cleaned_data.get("new_password1"):
        update_session_auth_hash(request, user)
    if request.headers.get("X-Requested-With") != "XMLHttpRequest":
        return redirect("dashboard_home")

    payload = build_dashboard_payload(user)
    return JsonResponse(
        {
            "ok": True,
            "message": "Profile updated.",
            "payload": payload,
            "user": {
                "display_name": user.first_name or user.username,
                "first_name": user.first_name,
                "username": user.username,
                "email": user.email,
            },
        }
    )
