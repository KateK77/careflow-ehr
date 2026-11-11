import uuid

from django import forms
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods, require_safe

from careflow.clinical.access import charts_for
from careflow.patients.access import roles_for
from careflow.patients.models import Patient
from .access import is_operator, require_operator, stays_for
from .models import AdmissionRequest, Bed, Department, Room, Ward
from .services import FACILITIES, add_facility, available_beds, change_stay, decide_admission, physicians, request_admission


EVENTS = {
    "hospital_admission_request": "Admission requested", "hospital_admit": "Admitted and bed assigned",
    "hospital_admission_cancel": "Admission request cancelled", "hospital_transfer": "Bed transfer",
    "hospital_discharge_plan": "Discharge plan documented", "hospital_discharge": "Discharged and bed released",
}
STAY_ACTIONS = {
    "hospital_transfer": "Transfer to another bed", "hospital_discharge_plan": "Save discharge plan",
    "hospital_discharge": "Confirm discharge and release bed",
}


class CommandForm(forms.Form):
    key = forms.UUIDField(initial=uuid.uuid4, widget=forms.HiddenInput)


class TransitionForm(CommandForm):
    version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    confirmed = forms.BooleanField(label="Confirm this fictional action")


class FacilityForm(CommandForm):
    name = forms.CharField(max_length=80, label="Fictional name")
    parent = forms.ModelChoiceField(queryset=None)
    ward_kind = forms.ChoiceField(choices=Ward._meta.get_field("kind").choices)

    def __init__(self, *args, kind, **kwargs):
        super().__init__(*args, **kwargs)
        parent_models = {"ward": Department, "room": Ward, "bed": Room}
        if kind in parent_models:
            self.fields["parent"].queryset = parent_models[kind].objects.all()
            if kind == "bed":
                self.fields["parent"].queryset = Room.objects.filter(ward__kind="inpatient")
        else:
            del self.fields["parent"]
        if kind != "ward":
            del self.fields["ward_kind"]


class RequestForm(CommandForm):
    patient = forms.ModelChoiceField(queryset=Patient.objects.all())
    reason = forms.CharField(max_length=240, label="Fictional admission reason")


class AdmitForm(TransitionForm):
    action = forms.ChoiceField(choices=[("hospital_admit", "Admit and allocate bed"),
                                       ("hospital_admission_cancel", "Cancel request")])
    bed = forms.ModelChoiceField(queryset=Bed.objects.all(), required=False)
    attending = forms.ModelChoiceField(queryset=None, required=False)
    reason = forms.CharField(max_length=240, required=False, label="Cancellation reason")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["attending"].queryset = physicians()
        if not self.is_bound:
            self.fields["bed"].queryset = available_beds()


class StayForm(TransitionForm):
    action = forms.ChoiceField(choices=STAY_ACTIONS.items())
    bed = forms.ModelChoiceField(queryset=Bed.objects.all(), required=False, label="Destination bed")
    note = forms.CharField(max_length=2000, label="Fictional plan, transfer reason or discharge summary",
                           widget=forms.Textarea(attrs={"rows": 4}))

    def __init__(self, *args, allowed, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            self.fields["action"].choices = [(key, STAY_ACTIONS[key]) for key in allowed]
            self.fields["bed"].queryset = available_beds()


def submit(form, callback):
    if form.is_valid():
        try:
            return callback(dict(form.cleaned_data))
        except ValidationError as exc:
            form.add_error(None, exc.messages)
    return None


def readable_events(query):
    return [(EVENTS.get(item.audit.action, "Hospital activity"), item.actor, item.audit.occurred_at,
             item.previous_bed, item.next_bed, item.details.get("note") or item.details.get("reason"))
            for item in query.select_related("audit", "actor", "previous_bed", "next_bed")]


def require_reader(user):
    if not is_operator(user) and not set(roles_for(user)) & {"Physician", "Nurse"}:
        raise PermissionDenied


def chart_context(user, patient):
    return {"inpatient_summary": stays_for(user).filter(request__patient=patient).order_by("-pk")[:10]}


@never_cache
@require_safe
def dashboard(request):
    require_reader(request.user)
    items = stays_for(request.user).order_by("-admitted_at")
    if request.GET.get("status") in ("active", "discharged"):
        items = items.filter(status=request.GET["status"])
    return render(request, "hospital/dashboard.html", {
        "items": [(item, (item.discharged_at or timezone.now()) - item.admitted_at) for item in items],
    })


@never_cache
@require_safe
def capacity(request):
    require_operator(request.user)
    beds = Bed.objects.select_related("room__ward__department").order_by("room__ward__department__name", "room__ward__name", "room__name", "name")
    open_ids = set(available_beds().values_list("pk", flat=True))
    return render(request, "hospital/capacity.html", {"beds": [(bed, bed.pk in open_ids) for bed in beds],
                                                       "open_count": len(open_ids)})


@never_cache
@require_http_methods(["GET", "POST"])
def facilities(request, kind="department"):
    require_operator(request.user)
    model = FACILITIES.get(kind)
    if model is None:
        raise Http404
    form = FacilityForm(request.POST if request.method == "POST" else None, kind=kind)
    if request.method == "POST":
        def save(data):
            parent = data.get("parent")
            return add_facility(request.user, kind, data["name"], parent.pk if parent else None,
                                data.get("ward_kind"), data["key"])
        if submit(form, save):
            return redirect("hospital_facility", kind)
    return render(request, "hospital/facilities.html", {"form": form, "kind": kind, "items": model.objects.all()},
                  status=400 if form.errors else 200)


@never_cache
@require_http_methods(["GET", "POST"])
def admissions(request):
    require_operator(request.user)
    form = RequestForm(request.POST if request.method == "POST" else None)
    if request.method == "POST":
        item = submit(form, lambda data: request_admission(
            request.user, data["patient"].pk, data["reason"], data["key"],
        ))
        if item:
            return redirect("hospital_admission", item.patient_id, item.pk)
    return render(request, "hospital/admissions.html", {"form": form, "items": AdmissionRequest.objects.select_related(
        "patient", "stay").order_by("-created_at")}, status=400 if form.errors else 200)


@never_cache
@require_http_methods(["GET", "POST"])
def admission(request, patient_id, request_id):
    require_operator(request.user)
    item = get_object_or_404(AdmissionRequest.objects.select_related("patient", "stay"), pk=request_id,
                             patient_id=patient_id)
    form = AdmitForm(request.POST if request.method == "POST" else None, initial={"version": item.version})
    if request.method == "POST":
        def save(data):
            bed, attending = data.pop("bed"), data.pop("attending")
            return decide_admission(request.user, item.pk, bed_id=bed.pk if bed else None,
                                    attending_id=attending.pk if attending else None, **data)
        if submit(form, save):
            return redirect("hospital_admission", patient_id, item.pk)
    return render(request, "hospital/admission.html", {"form": form, "item": item,
                  "history": readable_events(item.events.all())}, status=400 if form.errors else 200)


@never_cache
@require_http_methods(["GET", "POST"])
def stay(request, patient_id, stay_id):
    require_reader(request.user)
    item = get_object_or_404(stays_for(request.user), pk=stay_id, request__patient_id=patient_id)
    patient = item.request.patient
    actions = []
    if item.status == "active":
        if is_operator(request.user):
            actions.append("hospital_transfer")
            if item.discharge_plan:
                actions.append("hospital_discharge")
        if request.user.pk == item.attending_id and "Physician" in roles_for(request.user):
            actions.append("hospital_discharge_plan")
    form = StayForm(request.POST if request.method == "POST" else None, allowed=actions,
                    initial={"version": item.version})
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "hospital_discharge_plan":
            if request.user.pk != item.attending_id or "Physician" not in roles_for(request.user):
                raise PermissionDenied
        else:
            require_operator(request.user)

        def save(data):
            bed = data.pop("bed")
            return change_stay(request.user, patient_id, item.pk, bed_id=bed.pk if bed else None, **data)
        if submit(form, save):
            return redirect("hospital_stay", patient_id, item.pk)
    chart_access = bool(set(roles_for(request.user)) & {"Administrator", "Physician", "Nurse"})
    return render(request, "hospital/stay.html", {
        "form": form, "item": item, "patient": patient, "actions": actions,
        "can_open_chart": chart_access and charts_for(request.user).filter(pk=patient_id).exists(),
        "duration": (item.discharged_at or timezone.now()) - item.admitted_at,
        "history": readable_events(item.events.all()),
    }, status=400 if form.errors else 200)
