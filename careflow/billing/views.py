import uuid
from functools import wraps

from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.cache import add_never_cache_headers
from django.views.decorators.http import require_http_methods, require_safe

from careflow.patients.models import Patient
from careflow.portal.access import patient_only

from .access import require_billing
from .models import BillingEvent, ChargeCatalog, EncounterCharge, PatientCoverage, PatientStatement
from .services import change_statement, create_catalog, create_coverage, eligible_encounters


ACTIONS = {
    "billing_catalog_add": "Catalog revision added", "billing_coverage_add": "Coverage revision added",
    "billing_charge_add": "Charge added", "billing_charge_edit": "Charge updated",
    "billing_charge_void": "Draft charge voided", "billing_statement_void": "Draft statement voided",
    "billing_finalize": "Statement finalized", "billing_release": "Statement released",
}


def staff_only(view):
    @wraps(view)
    def checked(request, *args, **kwargs):
        require_billing(request.user)
        response = view(request, *args, **kwargs)
        add_never_cache_headers(response)
        return response
    return checked


class CommandForm(forms.Form):
    key = forms.UUIDField(widget=forms.HiddenInput, initial=uuid.uuid4)
    version = forms.IntegerField(min_value=0, label="Current revision", initial=0)


class CatalogForm(CommandForm):
    code = forms.CharField(max_length=32, help_text="Use a fictional SYN- code.")
    description = forms.CharField(max_length=120)
    unit_cents = forms.IntegerField(min_value=1, max_value=10000000, label="Fictional price in cents")


class CoverageForm(CommandForm):
    patient = forms.ModelChoiceField(queryset=Patient.objects.order_by("mrn"))
    policy = forms.CharField(max_length=40, help_text="Use a fictional SYN- policy identifier.")
    payer = forms.CharField(max_length=80, help_text="Start the payer name with Synthetic.")
    coverage_type = forms.ChoiceField(choices=PatientCoverage._meta.get_field("coverage_type").choices)
    status = forms.ChoiceField(choices=PatientCoverage._meta.get_field("status").choices)
    effective_from = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    effective_to = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))


STATEMENT_ACTIONS = {
    "billing_charge_add": "Add draft charge", "billing_charge_edit": "Edit draft quantity",
    "billing_charge_void": "Void draft charge", "billing_statement_void": "Void draft statement",
    "billing_finalize": "Finalize statement", "billing_release": "Release statement to patient",
}


class StatementForm(CommandForm):
    version = forms.IntegerField(min_value=0, widget=forms.HiddenInput)
    action = forms.ChoiceField(choices=STATEMENT_ACTIONS.items())
    catalog = forms.ModelChoiceField(queryset=ChargeCatalog.objects.all(), required=False)
    charge = forms.ModelChoiceField(queryset=EncounterCharge.objects.none(), required=False,
                                    help_text="Select an existing charge to edit or void.")
    quantity = forms.IntegerField(min_value=1, max_value=100, required=False)
    confirmed = forms.BooleanField(label="Confirm this fictional billing action")

    def __init__(self, *args, statement, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            allowed = {
                None: ["billing_charge_add"],
                "draft": [key for key in STATEMENT_ACTIONS if key != "billing_release"],
                "finalized": ["billing_release"],
            }
            self.fields["action"].choices = [(key, STATEMENT_ACTIONS[key]) for key in
                                             allowed.get(statement.status if statement else None, [])]
        if statement:
            self.fields["charge"].queryset = statement.charges.select_related("catalog")
            self.fields["charge"].label_from_instance = lambda line: f"{line.pk} · {line.catalog.code} · quantity {line.quantity}"


class WorklistFilter(forms.Form):
    search = forms.CharField(required=False, max_length=80, label="Patient name or MRN")
    encounter = forms.IntegerField(required=False, min_value=1)
    status = forms.ChoiceField(required=False, choices=[("", "All"), ("unbilled", "Unbilled"),
                                                        *PatientStatement._meta.get_field("status").choices])
    since = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))


def submit(form, callback):
    if form.is_valid():
        try:
            return callback(dict(form.cleaned_data))
        except ValidationError as exc:
            form.add_error(None, exc.messages)
    return None


def event_rows(subject, item_id, labels=ACTIONS):
    return [(labels.get(event.audit.action, "Financial event"), event.version, event.actor,
             event.audit.occurred_at) for event in BillingEvent.objects.filter(subject=subject, subject_id=item_id)
            .select_related("audit", "actor")]


def money(cents):
    return f"${cents // 100:,}.{cents % 100:02d}"


@require_safe
@staff_only
def worklist(request):
    form = WorklistFilter(request.GET)
    items = eligible_encounters().select_related("patient", "patientstatement").order_by("-completed_at")
    if form.is_valid():
        data = form.cleaned_data
        if search := data["search"]:
            items = items.filter(Q(patient__mrn__icontains=search) | Q(patient__first_name__icontains=search)
                                 | Q(patient__last_name__icontains=search))
        if data["encounter"]:
            items = items.filter(pk=data["encounter"])
        if data["since"]:
            items = items.filter(completed_at__date__gte=data["since"])
        if data["status"] == "unbilled":
            items = items.filter(patientstatement__isnull=True)
        elif data["status"]:
            items = items.filter(patientstatement__status=data["status"])
    return render(request, "billing/worklist.html", {"items": items[:100], "form": form})


@require_http_methods(["GET", "POST"])
@staff_only
def catalog(request):
    form = CatalogForm(request.POST if request.method == "POST" else None)
    if request.method == "POST":
        def save(data):
            version, key = data.pop("version"), data.pop("key")
            return create_catalog(request.user, data, version, key)
        if submit(form, save):
            return redirect("billing_catalog")
    rows = [(item.code, item.revision, item.description, money(item.unit_cents)) for item in ChargeCatalog.objects.all()]
    return render(request, "billing/configuration.html", {
        "title": "Synthetic Charge Catalog", "form": form, "headers": ["Code", "Revision", "Description", "Price"],
        "rows": rows,
    }, status=400 if form.errors else 200)


@require_http_methods(["GET", "POST"])
@staff_only
def coverage(request):
    form = CoverageForm(request.POST if request.method == "POST" else None)
    if request.method == "POST":
        def save(data):
            patient, version, key = data.pop("patient"), data.pop("version"), data.pop("key")
            return create_coverage(request.user, patient.pk, data, version, key)
        if submit(form, save):
            return redirect("billing_coverage")
    return render(request, "billing/configuration.html", {
        "title": "Coverage Management", "form": form,
        "headers": ["Patient", "Policy", "Revision", "Payer", "Type", "Status", "Effective from", "Effective to"],
        "rows": coverage_rows(PatientCoverage.objects.select_related("patient"), staff=True),
    }, status=400 if form.errors else 200)


def coverage_rows(items, staff=False):
    return [((item.patient,) if staff else ()) + (
        item.policy if staff else item.payer, item.revision,
    ) + ((item.payer,) if staff else ()) + (
        item.get_coverage_type_display(), item.get_status_display(), item.effective_from, item.effective_to or "Open-ended",
    ) for item in items]


@require_http_methods(["GET", "POST"])
@staff_only
def encounter(request, encounter_id):
    visit = get_object_or_404(eligible_encounters().select_related("patient"), pk=encounter_id)
    item = PatientStatement.objects.filter(encounter=visit).first()
    form = StatementForm(request.POST if request.method == "POST" else None, statement=item,
                         initial={"version": item.version if item else 0})
    if request.method == "POST":
        def save(data):
            catalog_item, charge = data["catalog"], data["charge"]
            return change_statement(request.user, visit.pk, data["version"], data["key"], data["action"],
                                    catalog_id=catalog_item.pk if catalog_item else None,
                                    charge_id=charge.pk if charge else None, quantity=data["quantity"])
        if submit(form, save):
            return redirect("billing_encounter", visit.pk)
    return render(request, "billing/statement.html", statement_context(item, visit, form), status=400 if form.errors else 200)


def statement_context(item, visit, form=None):
    staff = form is not None
    lines = []
    if item and item.status in ("finalized", "released"):
        lines = [(line.code, line.description, line.quantity, money(line.unit_cents),
                  money(line.subtotal_cents), "Finalized") for line in item.lines.all()]
    elif item and staff:
        lines = [(line.catalog.code, line.catalog.description, line.quantity, money(line.catalog.unit_cents),
                  money(line.subtotal_cents), "Voided" if line.void else "Draft")
                 for line in item.charges.select_related("catalog")]
    total = item.total_cents if item else 0
    if item and item.status == "draft":
        total = sum(line.subtotal_cents for line in item.charges.filter(void=False).select_related("catalog"))
    balance = total
    financial_status = "Balance due" if total else "No balance"
    if item and item.status == "released":
        from .claims import position
        summary = position(item)
        balance = summary["patient_due"] + (summary["payer_due"] if staff else 0)
        financial_status = summary["status"]
    return {"layout": "core/base.html" if staff else "portal/base.html", "item": item, "visit": visit,
            "form": form, "lines": lines, "total": money(total), "balance": money(balance),
            "financial_status": financial_status,
            "history": event_rows("statement", item.pk) if item and staff else []}


def released_statements(patient):
    return PatientStatement.objects.filter(encounter__patient=patient, status="released").select_related("encounter")


@require_safe
@patient_only
def portal_list(request, patient):
    return render(request, "billing/portal_list.html", {
        "patient": patient,
        "items": [(item, money(item.total_cents)) for item in released_statements(patient).order_by("-released_at")],
        "coverage": coverage_rows(PatientCoverage.objects.filter(patient=patient)),
    })


@require_safe
@patient_only
def portal_detail(request, patient, statement_id):
    item = get_object_or_404(released_statements(patient), pk=statement_id)
    return render(request, "billing/statement.html", {**statement_context(item, item.encounter), "patient": patient})
