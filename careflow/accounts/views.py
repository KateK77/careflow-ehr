from functools import wraps
from django.core.exceptions import ValidationError
from django.db import IntegrityError, OperationalError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from django.views.decorators.debug import sensitive_post_parameters
from . import services
from .forms import ReviewForm, SignupForm
from .models import Enrollment


def admin_only(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not services.is_account_admin(request.user):
            return render(request, "core/403.html", status=403)
        return view(request, *args, **kwargs)
    return wrapped


@sensitive_post_parameters()
@require_http_methods(["GET", "POST"])
def signup(request, kind):
    if kind not in ("patient", "staff"):
        raise Http404
    form = SignupForm(request.POST or None, kind=kind)
    if request.method == "POST" and form.is_valid():
        try:
            services.register(kind, form.cleaned_data)
        except IntegrityError:
            form.add_error("username", "This username is unavailable. Choose another.")
        except ValidationError as error:
            form.add_error(None, error)
        except OperationalError:
            return render(request, "accounts/unavailable.html", status=503)
        else:
            return redirect("account_complete", kind=kind)
    return render(request, "accounts/form.html", {"form": form,
        "title": "Create a patient account" if kind == "patient" else "Apply for staff access",
        "intro": ("Create a separate fictional patient account using a username and password."
                  if kind == "patient" else "Choose a username and password. An Administrator must approve your staff role before you can sign in."),
        "button": "Create patient account" if kind == "patient" else "Submit staff application"})


@require_http_methods(["GET"])
def complete(request, kind):
    if kind not in ("patient", "staff"):
        raise Http404
    return render(request, "accounts/complete.html", {"patient_account": kind == "patient"})


@require_http_methods(["GET"])
@admin_only
def applications(request):
    items = Enrollment.objects.filter(kind="staff").select_related("user", "reviewed_by").order_by("-created_at")
    from django.core.paginator import Paginator
    return render(request, "accounts/applications.html", {"page": Paginator(items, 25).get_page(request.GET.get("page"))})


@sensitive_post_parameters()
@require_http_methods(["GET", "POST"])
@admin_only
def application(request, pk):
    item = get_object_or_404(Enrollment.objects.select_related("user"), pk=pk, kind="staff")
    form = ReviewForm(request.POST or None, initial={"version": item.version, "role": item.requested_role})
    if request.method == "POST" and form.is_valid():
        try:
            services.review(request.user, item.pk, form.cleaned_data)
        except ValidationError as error:
            form.add_error(None, error)
        except OperationalError:
            return render(request, "accounts/unavailable.html", status=503)
        else:
            return redirect("account_applications")
    return render(request, "accounts/application.html", {"item": item, "form": form,
        "events": item.events.select_related("actor"), "eligible": item.status == "pending"})
