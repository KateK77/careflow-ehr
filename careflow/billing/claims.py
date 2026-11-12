import re

from django.core.exceptions import ValidationError
from django.utils import timezone

from careflow.medications.services import check_version, command_transaction

from .models import MockAdjudication, MockAppeal, MockClaim, PatientCoverage, PatientStatement, SimulatedPayment
from .services import _begin, _object, _record


DECIDED = {"approved", "partial", "denied"}
OPEN_APPEAL = {"draft", "submitted"}


def available_coverage(statement):
    date = timezone.localdate(statement.encounter.completed_at)
    records = PatientCoverage.objects.filter(patient_id=statement.encounter.patient_id)
    seen = set()
    eligible = []
    for record in records:
        if record.policy in seen:
            continue
        seen.add(record.policy)
        if (record.status == "active" and record.effective_from <= date
                and (record.effective_to is None or record.effective_to >= date)):
            eligible.append(record)
    return eligible


def _note(value, limit):
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > limit:
        raise ValidationError(f"Enter a fictional explanation of 1 to {limit} characters.")
    return value.strip()


def position(statement, claim=None):
    claim = claim if claim is not None else getattr(statement, "mock_claim", None)
    decision = claim.decisions.first() if claim else None
    payer_cents = decision.payer_cents if decision else 0
    patient_cents = statement.total_cents - payer_cents
    payments = list(statement.payments.all())
    paid = {"patient": 0, "payer": 0}
    for payment in payments:
        paid[payment.source] += -payment.cents if payment.reversal_of_id else payment.cents
    patient_due = patient_cents - paid["patient"]
    payer_due = payer_cents - paid["payer"]
    pending = bool(claim and (claim.status not in DECIDED or claim.appeals.filter(status__in=OPEN_APPEAL).exists()))
    if pending:
        status = "Responsibility under review"
    elif not patient_due and not payer_due:
        status = "Paid"
    elif paid["patient"] or paid["payer"]:
        status = "Partially paid"
    else:
        status = "Balance due"
    return {
        "claim": claim, "patient_responsibility": patient_cents, "payer_responsibility": payer_cents,
        "patient_due": patient_due, "payer_due": payer_due, "paid": paid, "status": status, "pending": pending,
        "version": f"{claim.version if claim else 0}:{len(payments)}", "payments": payments,
    }


@command_transaction
def create_claim(actor, statement_id, coverage_id, key, confirmed):
    identity, prior = _begin(actor, key, "billing_claim_create", statement_id, coverage_id, confirmed)
    if prior:
        return MockClaim.objects.get(pk=prior.subject_id)
    if confirmed is not True:
        raise ValidationError("Confirm use of the internal simulator.")
    statement = _object(PatientStatement.objects.select_related("encounter"), pk=statement_id,
                        status__in=["finalized", "released"])
    if MockClaim.objects.filter(statement=statement).exists() or statement.payments.exists():
        raise ValidationError("Only one claim can be created per statement, before payment activity.")
    coverage = next((record for record in available_coverage(statement) if record.pk == coverage_id), None)
    if coverage is None:
        raise ValidationError("Choose current synthetic coverage for this patient and encounter date.")
    claim = MockClaim.objects.create(statement=statement, coverage=coverage)
    _record(actor, statement.encounter.patient, "billing_claim_create", identity, "claim", claim, 1,
            coverage_revision=coverage.pk)
    return claim


def _decision(claim, outcome, payer_cents, denial, appeal=None):
    total = claim.statement.total_cents
    if type(payer_cents) is not int:
        raise ValidationError("Enter payer responsibility in whole cents.")
    if outcome == "denied":
        valid = payer_cents == 0 and denial in dict(MockAdjudication.DENIALS)
    elif outcome == "approved":
        valid = payer_cents == total and not denial
    elif outcome == "partial":
        valid = 0 < payer_cents < total and not denial
    else:
        valid = False
    if not valid:
        raise ValidationError("Match the simulated outcome, payer amount and denial category.")
    paid = position(claim.statement, claim)["paid"]
    if paid["payer"] > payer_cents or paid["patient"] > total - payer_cents:
        raise ValidationError("This allocation conflicts with posted payments. Review the ledger before proceeding.")
    claim.status = outcome
    MockAdjudication.objects.create(claim=claim, appeal=appeal, outcome=outcome, payer_cents=payer_cents,
                                    denial=denial, claim_version=claim.version)


@command_transaction
def change_claim(actor, claim_id, version, key, action, confirmed, *, outcome="", payer_cents=None, denial=""):
    identity, prior = _begin(actor, key, action, claim_id, version, confirmed, outcome, payer_cents, denial)
    claim = _object(MockClaim.objects.select_related("statement__encounter__patient"), pk=claim_id)
    if prior:
        return claim
    if confirmed is not True:
        raise ValidationError("Confirm use of the internal simulator.")
    check_version(version, claim.version)
    claim.version += 1
    if action == "billing_claim_submit" and claim.status == "draft":
        claim.status = "submitted"
    elif action == "billing_claim_queue" and claim.status == "submitted":
        claim.status = "pending"
    elif action == "billing_claim_decide" and claim.status == "pending":
        _decision(claim, outcome, payer_cents, denial)
    else:
        raise ValidationError("This action is unavailable in the current claim state.")
    claim.save(update_fields=["status", "version"])
    _record(actor, claim.statement.encounter.patient, action, identity, "claim", claim, claim.version,
            outcome=claim.status)
    return claim


@command_transaction
def change_appeal(actor, claim_id, claim_version, appeal_id, appeal_version, key, action, confirmed, *,
                  explanation="", line_id=None, resolution="", outcome="", payer_cents=None):
    identity, prior = _begin(actor, key, action, claim_id, claim_version, appeal_id, appeal_version, confirmed,
                             explanation, line_id, resolution, outcome, payer_cents)
    claim = _object(MockClaim.objects.select_related("statement__encounter__patient"), pk=claim_id)
    if prior:
        return MockAppeal.objects.get(pk=prior.subject_id)
    if confirmed is not True or claim.status != "denied":
        raise ValidationError("Confirm an available simulated appeal action on a denied claim.")
    check_version(claim_version, claim.version)
    if appeal_id is None:
        if action != "billing_appeal_save" or claim.appeals.filter(status__in=OPEN_APPEAL).exists():
            raise ValidationError("Only one open appeal is allowed.")
        appeal = MockAppeal(claim=claim, version=0)
    else:
        appeal = _object(claim.appeals, pk=appeal_id)
    check_version(appeal_version, appeal.version)
    claim.version += 1
    appeal.version += 1
    if action == "billing_appeal_save" and appeal.status == "draft":
        appeal.explanation = _note(explanation, 500)
        appeal.supporting_line = _object(claim.statement.lines, pk=line_id) if line_id is not None else None
    elif action == "billing_appeal_submit" and appeal.status == "draft":
        appeal.status = "submitted"
    elif action in ("billing_appeal_uphold", "billing_appeal_overturn") and appeal.status == "submitted":
        appeal.resolution = _note(resolution, 240)
        appeal.status = "upheld" if action == "billing_appeal_uphold" else "overturned"
    else:
        raise ValidationError("This action is unavailable in the current appeal state.")
    appeal.save()
    if action == "billing_appeal_uphold":
        denial = claim.decisions.first().denial
        _decision(claim, "denied", 0, denial, appeal)
    elif action == "billing_appeal_overturn":
        _decision(claim, outcome, payer_cents, "", appeal)
    claim.save(update_fields=["status", "version"])
    _record(actor, claim.statement.encounter.patient, action, identity, "appeal", appeal, appeal.version,
            explanation=appeal.explanation, line=appeal.supporting_line_id, resolution=appeal.resolution,
            outcome=appeal.status)
    return appeal


@command_transaction
def record_payment(actor, statement_id, balance_version, key, confirmed, reference, *, source="", cents=None,
                   reversal_id=None, reason=""):
    action = "billing_payment_reverse" if reversal_id is not None else "billing_payment_post"
    identity, prior = _begin(actor, key, action, statement_id, balance_version, confirmed, reference, source,
                             cents, reversal_id, reason)
    if prior:
        return SimulatedPayment.objects.get(pk=prior.subject_id)
    statement = _object(PatientStatement.objects.select_related("encounter__patient"),
                        pk=statement_id, status="released")
    if confirmed is not True or not isinstance(reference, str) or not re.fullmatch(r"SYN-[A-Z0-9-]{1,36}", reference):
        raise ValidationError("Confirm the action and enter a unique fictional SYN- transaction reference.")
    summary = position(statement)
    if summary["version"] != balance_version:
        raise ValidationError("The balance changed. Reload the statement before proceeding.")
    original = None
    if reversal_id is not None:
        original = _object(statement.payments, pk=reversal_id, reversal_of__isnull=True)
        if hasattr(original, "reversal"):
            raise ValidationError("This payment has already been reversed.")
        reason = _note(reason, 240)
        source, cents = original.source, original.cents
    elif (summary["pending"] or source not in dict(SimulatedPayment.SOURCE)
          or type(cents) is not int or not 0 < cents <= summary[source + "_due"]):
        raise ValidationError("Enter a positive amount within the available simulated balance for this source.")
    if SimulatedPayment.objects.filter(reference=reference).exists():
        raise ValidationError("Use a unique fictional transaction reference.")
    payment = SimulatedPayment.objects.create(statement=statement, source=source, cents=cents, reference=reference,
                                             recorder=actor, reversal_of=original)
    _record(actor, statement.encounter.patient, action, identity, "payment", payment, len(summary["payments"]) + 1,
            source=source, cents=cents, reversal_of=reversal_id, reason=reason)
    return payment
