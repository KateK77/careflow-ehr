from django import forms
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from careflow.clinical.access import charts_for
from careflow.patients.access import roles_for
from careflow.patients.models import Patient
from .access import is_operator, require_operator, stays_for
from .emergency import ACTIONS, advance_ed, allowed_role, ed_reader, free_ed_rooms, register_ed, visits_for, wait_minutes
from .models import Bed, EmergencyVisit, Room
from .services import available_beds, physicians
from .views import CommandForm, TransitionForm, submit


class RegistrationForm(CommandForm):
    patient = forms.ModelChoiceField(queryset=Patient.objects.all())
    arrival_method = forms.ChoiceField(choices=EmergencyVisit.ARRIVAL_METHODS)
    complaint = forms.CharField(max_length=240, label="Fictional chief complaint")
    confirmed = forms.BooleanField(label="Confirm synthetic ED registration")


class EDForm(TransitionForm):
    action = forms.ChoiceField(choices=ACTIONS.items())
    category = forms.ChoiceField(choices=[("", "Select for triage"), *EmergencyVisit.TRIAGE],
                                 required=False, label="Fictional triage label")
    room = forms.ModelChoiceField(queryset=Room.objects.filter(ward__kind="ed"), required=False)
    clinician = forms.ModelChoiceField(queryset=None, required=False)
    bed = forms.ModelChoiceField(queryset=Bed.objects.all(), required=False, label="Inpatient bed")
    note = forms.CharField(max_length=500, required=False, label="Synthetic triage observation or disposition summary",
                           widget=forms.Textarea(attrs={"rows": 3}))

    def __init__(self, *args, actions, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["clinician"].queryset = physicians()
        if not self.is_bound:
            self.fields["action"].choices = [(action, ACTIONS[action]) for action in actions]
            self.fields["room"].queryset = free_ed_rooms()
            self.fields["bed"].queryset = available_beds()
            for field, related in {
                "category": {"ed_triage"}, "room": {"ed_room"}, "clinician": {"ed_room"},
                "bed": {"ed_admit"}, "note": {"ed_triage", "ed_discharge", "ed_admit"},
            }.items():
                if not set(actions) & related:
                    del self.fields[field]


@never_cache
@require_http_methods(["GET", "POST"])
def board(request):
    if not ed_reader(request.user):
        raise PermissionDenied
    form = None
    if is_operator(request.user):
        form = RegistrationForm(request.POST if request.method == "POST" else None)
    if request.method == "POST":
        require_operator(request.user)
        def save(data):
            patient = data.pop("patient")
            return register_ed(request.user, patient.pk, **data)
        item = submit(form, save)
        if item:
            return redirect("ed_visit", item.patient_id, item.pk)
    rows = visits_for(request.user).order_by("-arrived_at")
    if request.GET.get("status") in dict(EmergencyVisit.STATES):
        rows = rows.filter(status=request.GET["status"])
    return render(request, "hospital/ed_board.html", {
        "form": form, "rows": [(item, wait_minutes(item)) for item in rows], "states": EmergencyVisit.STATES,
    }, status=400 if form and form.errors else 200)


def _actions(actor, visit):
    transitions = {
        "waiting": ["ed_triage"], "triage": ["ed_triage", "ed_room"], "roomed": ["ed_provider"],
        "provider": ["ed_observation", "ed_discharge", "ed_admit"], "observation": ["ed_discharge", "ed_admit"],
    }
    return [action for action in transitions.get(visit.status, []) if allowed_role(actor, action, visit)]


@never_cache
@require_http_methods(["GET", "POST"])
def visit_detail(request, patient_id, visit_id):
    if not ed_reader(request.user):
        raise PermissionDenied
    item = get_object_or_404(visits_for(request.user), pk=visit_id, patient_id=patient_id)
    actions = _actions(request.user, item)
    form = EDForm(request.POST if request.method == "POST" else None, actions=actions, initial={"version": item.version})
    if request.method == "POST":
        if not allowed_role(request.user, request.POST.get("action"), item):
            raise PermissionDenied

        def save(data):
            for field in ("room", "clinician", "bed"):
                target = data.pop(field)
                data[field + "_id"] = target.pk if target else None
            return advance_ed(request.user, patient_id, item.pk, **data)
        if submit(form, save):
            return redirect("ed_visit", patient_id, item.pk)
    can_chart = bool(set(roles_for(request.user)) & {"Administrator", "Physician", "Nurse"})
    state_labels, triage_labels = dict(EmergencyVisit.STATES), dict(EmergencyVisit.TRIAGE)
    history = []
    for event in item.events.select_related("audit", "actor"):
        details = event.details
        history.append({
            "label": ACTIONS.get(event.audit.action, "ED arrival registered"), "actor": event.actor,
            "at": event.audit.occurred_at, "before": state_labels.get(details.get("before")),
            "after": state_labels.get(details.get("after")), "category": triage_labels.get(details.get("category")),
            "note": details.get("note"), "room": details.get("room") or details.get("released_room"),
            "clinician": details.get("clinician"),
        })
    return render(request, "hospital/ed_visit.html", {
        "item": item, "form": form, "actions": actions, "history": history, "wait": wait_minutes(item),
        "can_chart": can_chart and charts_for(request.user).filter(pk=patient_id).exists(),
        "can_open_stay": bool(item.inpatient_stay_id and stays_for(request.user).filter(pk=item.inpatient_stay_id).exists()),
    }, status=400 if form.errors else 200)
