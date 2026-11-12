from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView, LogoutView
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_safe

from careflow.history.models import MedicationStatement
from careflow.medications.models import MedicationOrder
from careflow.patients.access import roles_for
from careflow.patients.models import AuditEvent
from careflow.scheduling.models import Appointment
from careflow.clinical.models import Encounter
from .access import patient_for, patient_only
from .communication import conversations, with_unread
from .records import display_result, eligible_results, patient_results, release_result


class PortalLoginForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if patient_for(user) is None:
            raise self.get_invalid_login_error()


class PortalLogin(LoginView):
    template_name = "portal/login.html"
    authentication_form = PortalLoginForm

    def get_success_url(self):
        return str(reverse_lazy("portal_home"))

    def form_valid(self, form):
        user = form.get_user()
        AuditEvent.objects.create(actor=user, patient=patient_for(user), action="portal_login")
        return super().form_valid(form)


class PortalLogout(LogoutView):
    next_page = reverse_lazy("portal_login")

    def post(self, request, *args, **kwargs):
        patient = patient_for(request.user)
        if patient is None:
            raise PermissionDenied
        AuditEvent.objects.create(actor=request.user, patient=patient, action="portal_logout")
        return super().post(request, *args, **kwargs)


def local_time(value):
    return timezone.localtime(value).strftime("%Y-%m-%d %H:%M %Z") if value else ""


def appointment_rows(query):
    return [(local_time(item.start_at), local_time(item.end_at), str(item.physician),
             item.appointment_type, item.get_status_display(),
             item.encounter.get_status_display() if hasattr(item, "encounter") else "No visit started")
            for item in query.select_related("physician", "encounter")]


def visit_rows(query):
    return [(local_time(v.completed_at), str(v.physician), v.appointment.appointment_type)
            for v in query.select_related("appointment", "physician")]


def medication_tables(patient, limit):
    history = MedicationStatement.objects.filter(patient=patient).order_by("-pk")[:limit]
    orders = MedicationOrder.objects.filter(
        encounter__patient=patient, signed_at__isnull=False, status__in=["signed", "cancelled"],
    ).select_related("pharmacy_review__dispense").order_by("-signed_at")[:limit]
    return [
        {"title": "Medication history statements", "headers": ["Medication", "Reported dose", "History status"],
         "rows": [(item.label, item.dose, item.get_status_display()) for item in history]},
        {"title": "Signed medication orders", "headers": ["Medication", "Proposed dose", "Order status", "Pharmacy"],
         "rows": [(item.catalog_snapshot["name"], item.dose, item.get_status_display(),
                   ("Simulated dispensing recorded" if hasattr(item.pharmacy_review, "dispense")
                    else item.pharmacy_review.get_status_display()) if hasattr(item, "pharmacy_review") else "No review recorded")
                  for item in orders]},
    ]


APPOINTMENT_HEADERS = ["Starts", "Ends", "Clinician", "Type", "Appointment status", "Visit status"]
VISIT_HEADERS = ["Completed", "Clinician", "Visit type"]


@require_safe
@patient_only
def dashboard(request, patient):
    visits = Encounter.objects.filter(patient=patient, status="completed").order_by("-completed_at")
    appointments = Appointment.objects.filter(patient=patient)
    now = timezone.now()
    tables = [
        {"title": "Upcoming appointments", "headers": APPOINTMENT_HEADERS,
         "rows": appointment_rows(appointments.filter(start_at__gte=now, status="scheduled")[:5])},
        {"title": "Recent appointment history", "headers": APPOINTMENT_HEADERS,
         "rows": appointment_rows(appointments.exclude(start_at__gte=now, status="scheduled").order_by("-start_at")[:5])},
        {"title": "Completed visits", "headers": VISIT_HEADERS, "rows": visit_rows(visits[:5])},
        *medication_tables(patient, 5),
    ]
    return render(request, "portal/records.html", {"title": "Patient dashboard", "patient": patient, "tables": tables,
                                                  "results": [display_result(r) for r in patient_results(patient)[:5]],
                                                  "show_results": True, "show_messages": True,
                                                  "unread": with_unread(conversations(request.user, patient), False).filter(unread=True).count()})


@require_safe
@patient_only
def records(request, patient, kind):
    notice = ""
    if kind == "appointments":
        tables = [{"title": "Appointments", "headers": APPOINTMENT_HEADERS,
                   "rows": appointment_rows(Appointment.objects.filter(patient=patient).order_by("-start_at"))}]
        title = "Appointment history"
    elif kind == "visits":
        tables = [{"title": "Completed visits", "headers": VISIT_HEADERS,
                   "rows": visit_rows(Encounter.objects.filter(patient=patient, status="completed").order_by("-completed_at"))}]
        title = "Visit records"
        notice = "No patient-facing visit summary has been published."
    else:
        tables = medication_tables(patient, None)
        title = "Medications"
        notice = "Pharmacy dispensing and medication administration are separate records."
    return render(request, "portal/records.html", {"title": title, "patient": patient, "tables": tables, "notice": notice})


@require_safe
@patient_only
def results(request, patient, result_id=None):
    query = patient_results(patient)
    rows = [get_object_or_404(query, pk=result_id)] if result_id is not None else query
    return render(request, "portal/records.html", {"title": "Laboratory results", "patient": patient,
                                                  "results": [display_result(r) for r in rows], "show_results": True})


@require_http_methods(["GET", "POST"])
def releases(request):
    if "Physician" not in roles_for(request.user):
        raise PermissionDenied
    error = ""
    if request.method == "POST":
        try:
            if request.POST.get("confirm") != "yes":
                raise ValidationError("Confirm release of the selected revision.")
            result_id = int(request.POST.get("result", ""))
            release_result(request.user, result_id, request.user.pk)
        except (ValueError, ValidationError) as exc:
            error = exc.messages[0] if isinstance(exc, ValidationError) else "Select a valid report revision."
        else:
            return redirect("portal_releases")
    candidates = eligible_results().filter(order__ordering_physician=request.user).select_related("order__patient", "portal_release")
    return render(request, "portal/releases.html", {"candidates": candidates, "error": error}, status=400 if error else 200)
