from datetime import date

from django.contrib import messages
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import F, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_safe

from .access import patient_access
from .forms import PATIENT_FIELDS, PatientForm
from .models import AuditEvent, Patient
from careflow.scheduling.access import appointments_for


@require_safe
@patient_access()
def dashboard(request):
    return render(request, "patients/dashboard.html", {"patient_count": Patient.objects.count()})


@require_safe
@patient_access()
def patient_list(request):
    query = request.GET.get("q", "").strip()[:120]
    sex = request.GET.get("sex", "")
    patients = Patient.objects.all()
    if query:
        match = (
            Q(mrn__icontains=query) | Q(first_name__icontains=query)
            | Q(last_name__icontains=query) | Q(phone__icontains=query)
        )
        parts = query.split()
        if len(parts) == 2:
            match |= Q(first_name__icontains=parts[0], last_name__icontains=parts[1])
        try:
            match |= Q(dob=date.fromisoformat(query))
        except ValueError:
            pass
        patients = patients.filter(match)
    if sex in Patient.Sex.values:
        patients = patients.filter(sex=sex)
    page = Paginator(patients, 15).get_page(request.GET.get("page"))
    return render(request, "patients/list.html", {
        "page": page, "query": query, "sex": sex, "sex_choices": Patient.Sex.choices,
    })


@require_safe
@patient_access()
def patient_detail(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    AuditEvent.objects.create(actor=request.user, patient=patient, action="patient_view")
    return render(request, "patients/detail.html", {
        "patient": patient,
        "appointments": appointments_for(request.user).filter(patient=patient).order_by("-updated_at")[:10],
        "events": patient.auditevent_set.filter(action__in=["patient_create", "patient_update"]).select_related("actor")[:10],
    })


@require_http_methods(["GET", "POST"])
@patient_access(write=True)
def patient_edit(request, pk=None):
    patient = get_object_or_404(Patient, pk=pk) if pk else Patient()
    form = PatientForm(request.POST if request.method == "POST" else None, instance=patient)
    conflict = False
    if request.method == "POST" and form.is_valid():
        values = {field: form.cleaned_data[field] for field in PATIENT_FIELDS}
        try:
            with transaction.atomic():
                if patient.pk:
                    # ModelForm updates its instance during validation. Fetch the stored values for the audit comparison.
                    stored = Patient.objects.get(pk=patient.pk)
                    changed = [field for field in PATIENT_FIELDS if getattr(stored, field) != values[field]]
                    updated = Patient.objects.filter(
                        pk=patient.pk, version=form.cleaned_data["version"],
                    ).update(**values, version=F("version") + 1, updated_at=timezone.now())
                    if not updated:
                        conflict = True
                    else:
                        AuditEvent.objects.create(
                            actor=request.user, patient=patient,
                            action="patient_update", changed_fields=changed,
                        )
                else:
                    patient = Patient.objects.create(**values)
                    AuditEvent.objects.create(
                        actor=request.user, patient=patient,
                        action="patient_create", changed_fields=list(PATIENT_FIELDS),
                    )
        except IntegrityError:
            form.add_error("mrn", "This MRN is already in use. Review it and try again.")
        else:
            if conflict:
                form.add_error(None, "This record changed after you opened it. Reload the patient before editing again.")
            else:
                messages.success(request, "Synthetic patient record saved.")
                return redirect("patient_detail", pk=patient.pk)
    return render(request, "patients/form.html", {"form": form, "patient": patient}, status=409 if conflict else 200)
