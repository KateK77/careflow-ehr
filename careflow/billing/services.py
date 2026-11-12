from django.core.exceptions import ValidationError
from django.db.models import F, Max
from django.utils import timezone

from careflow.clinical.models import Encounter
from careflow.medications.services import check_version, command_identity, command_transaction
from careflow.patients.models import AuditEvent, Patient

from .access import require_billing
from .models import BillingEvent, BillingLock, ChargeCatalog, EncounterCharge, PatientCoverage, PatientStatement, StatementLine


def eligible_encounters():
    return Encounter.objects.filter(status="completed", patient_id=F("appointment__patient_id"),
                                    physician_id=F("appointment__physician_id"))


def _lock():
    if not BillingLock.objects.filter(pk=1).update(revision=F("revision") + 1):
        BillingLock.objects.get_or_create(pk=1)
        BillingLock.objects.filter(pk=1).update(revision=F("revision") + 1)


def _begin(actor, key, action, *payload):
    require_billing(actor)
    _lock()
    identity = command_identity(key, action, *payload)
    prior = BillingEvent.objects.filter(actor=actor, key=identity[0]).first()
    if prior and prior.digest != identity[1]:
        raise ValidationError("This command was already used for different input. Refresh and try again.")
    return identity, prior


def _record(actor, patient, action, identity, subject, item, version, **details):
    audit = AuditEvent.objects.create(actor=actor, patient=patient, action=action)
    BillingEvent.objects.create(audit=audit, actor=actor, key=identity[0], digest=identity[1],
                                subject=subject, subject_id=item.pk, version=version, details=details)


def _object(query, **filters):
    item = query.filter(**filters).first()
    if item is None:
        raise ValidationError("The selected record is unavailable.")
    return item


@command_transaction
def create_catalog(actor, data, version, key):
    identity, prior = _begin(actor, key, "billing_catalog_add", data, version)
    if prior:
        return ChargeCatalog.objects.get(pk=prior.subject_id)
    code = data["code"].strip().upper()
    if not code.startswith("SYN-") or len(code) < 5:
        raise ValidationError("Use a fictional charge code beginning with SYN-.")
    current = ChargeCatalog.objects.filter(code=code).aggregate(value=Max("revision"))["value"] or 0
    check_version(version, current)
    cents = data["unit_cents"]
    if type(cents) is not int:
        raise ValidationError("Enter a whole number of cents.")
    item = ChargeCatalog(code=code, revision=current + 1, description=data["description"], unit_cents=cents)
    item.full_clean()
    item.save()
    _record(actor, None, "billing_catalog_add", identity, "catalog", item, item.revision)
    return item


@command_transaction
def create_coverage(actor, patient_id, data, version, key):
    identity, prior = _begin(actor, key, "billing_coverage_add", patient_id, data, version)
    if prior:
        return PatientCoverage.objects.get(pk=prior.subject_id)
    patient = _object(Patient.objects, pk=patient_id)
    policy = data["policy"].strip().upper()
    if not policy.startswith("SYN-") or len(policy) < 5 or not data["payer"].startswith("Synthetic "):
        raise ValidationError("Use a SYN- policy and a payer name beginning with Synthetic.")
    current = PatientCoverage.objects.filter(policy=policy).first()
    if current and current.patient_id != patient_id:
        raise ValidationError("The selected policy is unavailable for this patient.")
    check_version(version, current.revision if current else 0)
    item = PatientCoverage(patient=patient, revision=version + 1, **{**data, "policy": policy})
    item.full_clean()
    item.save()
    _record(actor, patient, "billing_coverage_add", identity, "coverage", item, item.revision)
    return item


@command_transaction
def change_statement(actor, encounter_id, version, key, action, *, catalog_id=None, charge_id=None, quantity=None):
    identity, prior = _begin(actor, key, action, encounter_id, version, catalog_id, charge_id, quantity)
    encounter = _object(eligible_encounters().select_related("patient"), pk=encounter_id)
    if prior:
        return _object(PatientStatement.objects, pk=prior.subject_id, encounter=encounter)
    item = PatientStatement.objects.filter(encounter=encounter).first()
    check_version(version, item.version if item else 0)
    if item is None:
        if action != "billing_charge_add":
            raise ValidationError("Add a charge to start a statement.")
        item = PatientStatement.objects.create(encounter=encounter, version=0)
    details = {}
    if action == "billing_release" and item.status == "finalized":
        item.status = "released"
        item.released_at = timezone.now()
    elif item.status != "draft":
        raise ValidationError("The statement is closed for this action.")
    elif action == "billing_finalize":
        _finalize(item)
    elif action == "billing_statement_void":
        item.status = "void"
    elif action in ("billing_charge_add", "billing_charge_edit", "billing_charge_void"):
        details = _change_charge(item, action, catalog_id, charge_id, quantity)
    else:
        raise ValidationError("Choose an available statement action.")
    item.version += 1
    item.save()
    _record(actor, encounter.patient, action, identity, "statement", item, item.version, **details)
    return item


def _change_charge(statement, action, catalog_id, charge_id, quantity):
    if action != "billing_charge_void" and (type(quantity) is not int or not 1 <= quantity <= 100):
        raise ValidationError("Enter a quantity from 1 to 100.")
    if action == "billing_charge_add":
        catalog = _object(ChargeCatalog.objects, pk=catalog_id)
        latest = ChargeCatalog.objects.filter(code=catalog.code).first()
        if catalog.pk != latest.pk:
            raise ValidationError("Choose the latest catalog revision.")
        charge = EncounterCharge.objects.create(statement=statement, catalog=catalog, quantity=quantity)
        return {"charge": charge.pk, "quantity": quantity, "unit_cents": catalog.unit_cents}
    charge = _object(statement.charges, pk=charge_id, void=False)
    before = charge.quantity
    if action == "billing_charge_edit":
        charge.quantity = quantity
    else:
        charge.void = True
    charge.save()
    return {"charge": charge.pk, "previous_quantity": before, "quantity": charge.quantity, "void": charge.void}


def _finalize(statement):
    charges = list(statement.charges.filter(void=False).select_related("catalog"))
    if not charges:
        raise ValidationError("At least one active charge is required.")
    for charge in charges:
        item = charge.catalog
        StatementLine.objects.create(statement=statement, charge=charge, code=item.code, revision=item.revision,
                                     description=item.description, unit_cents=item.unit_cents, quantity=charge.quantity)
    statement.total_cents = sum(charge.subtotal_cents for charge in charges)
    statement.finalized_at = timezone.now()
    statement.status = "finalized"
