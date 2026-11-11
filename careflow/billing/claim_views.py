import uuid

from django import forms
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_safe

from careflow.portal.access import patient_only

from .claims import available_coverage, change_appeal, change_claim, create_claim, position, record_payment
from .models import BillingEvent, MockAdjudication, MockAppeal, MockClaim, PatientCoverage, PatientStatement, SimulatedPayment
from .views import CommandForm, event_rows, money, released_statements, staff_only, submit


CLAIM_ACTIONS = {
    "billing_claim_create": "Draft created", "billing_claim_submit": "Submitted to simulator",
    "billing_claim_queue": "Queued for adjudication", "billing_claim_decide": "Adjudicated",
    "billing_appeal_save": "Appeal draft saved", "billing_appeal_submit": "Appeal submitted",
    "billing_appeal_uphold": "Denial upheld", "billing_appeal_overturn": "Denial overturned",
}
OUTCOMES = [("approved", "Approve"), ("partial", "Partially approve"), ("denied", "Deny")]


class ConfirmedCommand(CommandForm):
    version = forms.IntegerField(min_value=0, widget=forms.HiddenInput, required=False)
    confirmed = forms.BooleanField(label="Confirm fictional simulator action")


class ClaimCreateForm(ConfirmedCommand):
    coverage = forms.ModelChoiceField(queryset=PatientCoverage.objects.none(), label="Synthetic coverage revision")

    def __init__(self, *args, statement, **kwargs):
        super().__init__(*args, **kwargs)
        records = statement.encounter.patient.patientcoverage_set if self.is_bound else PatientCoverage.objects
        ids = [item.pk for item in available_coverage(statement)]
        self.fields["coverage"].queryset = records.all() if self.is_bound else records.filter(pk__in=ids)


class ClaimForm(ConfirmedCommand):
    action = forms.ChoiceField(choices=[
        ("billing_claim_submit", "Submit to internal simulator"), ("billing_claim_queue", "Queue for adjudication"),
        ("billing_claim_decide", "Record adjudication"),
    ])
    outcome = forms.ChoiceField(choices=[("", "Select for adjudication"), *OUTCOMES], required=False)
    payer_cents = forms.IntegerField(min_value=0, required=False, label="Simulated payer responsibility in cents")
    denial = forms.ChoiceField(choices=[("", "None"), *MockAdjudication.DENIALS], required=False)

    def __init__(self, *args, claim, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            selected = {"draft": "billing_claim_submit", "submitted": "billing_claim_queue",
                        "pending": "billing_claim_decide"}.get(claim.status)
            self.fields["action"].choices = [(key, label) for key, label in self.fields["action"].choices if key == selected]


class AppealForm(ConfirmedCommand):
    action = forms.ChoiceField(choices=[
        ("billing_appeal_save", "Save appeal draft"), ("billing_appeal_submit", "Submit appeal to simulator"),
        ("billing_appeal_uphold", "Uphold denial"), ("billing_appeal_overturn", "Overturn denial"),
    ])
    appeal = forms.ModelChoiceField(queryset=MockAppeal.objects.none(), widget=forms.HiddenInput, required=False)
    appeal_version = forms.IntegerField(min_value=0, widget=forms.HiddenInput)
    explanation = forms.CharField(max_length=500, widget=forms.Textarea(attrs={"rows": 3}), required=False)
    line = forms.ModelChoiceField(queryset=None, required=False, label="Supporting statement line")
    resolution = forms.CharField(max_length=240, required=False, label="Review explanation")
    outcome = forms.ChoiceField(choices=[("", "Select if overturning"), *OUTCOMES[:2]], required=False)
    payer_cents = forms.IntegerField(min_value=0, required=False, label="Revised payer responsibility in cents")

    def __init__(self, *args, claim, current, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["appeal"].queryset = claim.appeals.all()
        self.fields["line"].queryset = claim.statement.lines.all()
        self.fields["line"].label_from_instance = lambda line: f"{line.code} · {line.description}"
        if not self.is_bound:
            allowed = {"draft": ["billing_appeal_save", "billing_appeal_submit"],
                       "submitted": ["billing_appeal_uphold", "billing_appeal_overturn"]}
            choices = allowed.get(current.status, []) if current else ["billing_appeal_save"]
            self.fields["action"].choices = [(k, label) for k, label in self.fields["action"].choices if k in choices]


class PaymentForm(forms.Form):
    key = forms.UUIDField(widget=forms.HiddenInput)
    balance_version = forms.CharField(widget=forms.HiddenInput, max_length=40)
    reference = forms.CharField(max_length=40, label="Fictional transaction reference", help_text="Use SYN- followed by letters, numbers or hyphens.")
    source = forms.ChoiceField(choices=[("", "Select for a new payment"), *SimulatedPayment.SOURCE], required=False)
    cents = forms.IntegerField(min_value=1, required=False, label="Payment in cents")
    reversal = forms.ModelChoiceField(queryset=SimulatedPayment.objects.none(), required=False, label="Payment to reverse")
    reason = forms.CharField(max_length=240, required=False, label="Reason for reversal")
    confirmed = forms.BooleanField(label="Confirm this simulated transaction")

    def __init__(self, *args, statement, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["reversal"].queryset = statement.payments.filter(reversal_of__isnull=True)
        self.fields["reversal"].label_from_instance = lambda payment: f"{payment.reference} · {money(payment.cents)}"


def _claims():
    return MockClaim.objects.select_related("statement__encounter__patient", "coverage")


@require_safe
@staff_only
def worklist(request):
    return render(request, "billing/claims.html", {
        "claims": _claims().order_by("-pk"),
        "eligible": PatientStatement.objects.filter(status__in=["finalized", "released"], mock_claim__isnull=True,
                                                    payments__isnull=True).select_related("encounter__patient"),
    })


@require_http_methods(["GET", "POST"])
@staff_only
def new_claim(request, statement_id):
    statement = get_object_or_404(PatientStatement.objects.select_related("encounter__patient"),
                                  pk=statement_id, status__in=["finalized", "released"])
    form = ClaimCreateForm(request.POST if request.method == "POST" else None, statement=statement)
    if request.method == "POST":
        claim = submit(form, lambda data: create_claim(request.user, statement.pk, data["coverage"].pk,
                                                      data["key"], data["confirmed"]))
        if claim:
            return redirect("billing_claim", claim.pk)
    return render(request, "billing/claim_new.html", {"form": form, "item": statement, "total": money(statement.total_cents)},
                  status=400 if form.errors else 200)


def _history(subject, item_id):
    return event_rows(subject, item_id, CLAIM_ACTIONS)


@require_http_methods(["GET", "POST"])
@staff_only
def claim_detail(request, claim_id):
    claim = get_object_or_404(_claims(), pk=claim_id)
    current = claim.appeals.filter(status__in=["draft", "submitted"]).first()
    initial = {"version": claim.version}
    claim_form = ClaimForm(initial=initial, claim=claim)
    appeal_form = AppealForm(claim=claim, current=current, initial={
        **initial, "appeal": current, "appeal_version": current.version if current else 0,
        "explanation": current.explanation if current else "", "line": current.supporting_line if current else None,
    })
    if request.method == "POST":
        if request.POST.get("kind") == "appeal":
            appeal_form = AppealForm(request.POST, claim=claim, current=current)

            def save(data):
                appeal, line = data.pop("appeal"), data.pop("line")
                version, appeal_version = data.pop("version"), data.pop("appeal_version")
                return change_appeal(request.user, claim.pk, version, appeal.pk if appeal else None,
                                     appeal_version, line_id=line.pk if line else None, **data)
            changed = submit(appeal_form, save)
        else:
            claim_form = ClaimForm(request.POST, claim=claim)
            changed = submit(claim_form, lambda data: change_claim(request.user, claim.pk, **data))
        if changed:
            return redirect("billing_claim", claim.pk)
    decision_rows = [(decision.get_outcome_display(), money(decision.payer_cents),
                      decision.get_denial_display() or "None", decision.claim_version,
                      f"Appeal #{decision.appeal_id}" if decision.appeal_id else "Initial review")
                     for decision in claim.decisions.all()]
    summary = position(claim.statement, claim)
    return render(request, "billing/claim.html", {
        "claim": claim, "claim_form": claim_form, "appeal_form": appeal_form, "current": current,
        "total": money(claim.statement.total_cents), "decisions": decision_rows,
        "provisional": summary["pending"],
        "payer_responsibility": money(summary["payer_responsibility"]),
        "patient_responsibility": money(summary["patient_responsibility"]),
        "history": _history("claim", claim.pk), "line_rows": [
            (line.code, line.description, line.quantity, money(line.subtotal_cents))
            for line in claim.statement.lines.all()
        ],
        "appeals": [(item, _history("appeal", item.pk), BillingEvent.objects.filter(
            subject="appeal", subject_id=item.pk, audit__action="billing_appeal_save",
        ).select_related("audit").order_by("version")) for item in claim.appeals.all()],
    }, status=400 if claim_form.errors or appeal_form.errors else 200)


def _payment_context(item, patient=None):
    summary = position(item)
    staff = patient is None
    rows = []
    for entry in summary["payments"]:
        label = "Reversal" if entry.reversal_of_id else "Payment"
        values = (entry.get_source_display(), label, money(entry.cents), entry.recorded_at)
        rows.append(values + ((entry.reference, entry.recorder) if staff else ()))
    return {
        "layout": "core/base.html" if staff else "portal/base.html", "patient": patient, "item": item,
        "summary": summary, "total": money(item.total_cents),
        "patient_due": money(summary["patient_due"]), "payer_due": money(summary["payer_due"]),
        "overall_due": money(summary["patient_due"] + summary["payer_due"]), "rows": rows,
        "headers": ["Source", "Entry", "Amount", "Recorded"] + (["Reference", "Recorder"] if staff else []),
    }


@require_http_methods(["GET", "POST"])
@staff_only
def payments(request, statement_id):
    item = get_object_or_404(PatientStatement.objects.select_related("encounter__patient"),
                            pk=statement_id, status="released")
    context = _payment_context(item)
    form = PaymentForm(request.POST if request.method == "POST" else None, statement=item,
                       initial={"balance_version": context["summary"]["version"], "key": uuid.uuid4()})
    if request.method == "POST":
        def save(data):
            reversal = data.pop("reversal")
            return record_payment(request.user, item.pk, reversal_id=reversal.pk if reversal else None, **data)
        if submit(form, save):
            return redirect("billing_payments", item.pk)
    return render(request, "billing/payments.html", {**context, "form": form}, status=400 if form.errors else 200)


@require_safe
@patient_only
def portal_payments(request, patient, statement_id):
    item = get_object_or_404(released_statements(patient), pk=statement_id)
    return render(request, "billing/payments.html", _payment_context(item, patient))
