import re

from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone

from careflow.clinical.access import can_write
from careflow.medications.services import check_version, command_transaction
from careflow.scheduling.services import _lock_providers

from .access import is_radiology, orders_in_context
from .models import ExamWorkflow, ImagingReport, ImagingReview
from .services import receipt, record, schedule, text_value


REPORT_ACTIONS = {
    "imaging_report_draft", "imaging_preliminary", "imaging_final",
    "imaging_correct", "imaging_withdraw",
}


def current_report(order):
    return order.reports.exclude(status="draft").select_related("author", "review").first()


def workspace_orders(actor):
    if not is_radiology(actor):
        raise PermissionDenied
    return orders_in_context().filter(workflow__assigned_to=actor)


def available_orders(actor):
    if not is_radiology(actor):
        raise PermissionDenied
    return orders_in_context().filter(status="signed", workflow__isnull=True)


def _order(order_id, provider_id):
    _lock_providers([provider_id])
    order = orders_in_context().filter(pk=order_id, encounter__physician_id=provider_id).first()
    if order is None:
        raise PermissionDenied
    return order


@command_transaction
def radiology_command(actor, order_id, provider_id, action, version, key, confirmed, *, scheduled_at=None,
                      study_id="", body_site="", findings="", impression="", reason="", withdrawal_kind=""):
    if not is_radiology(actor):
        raise PermissionDenied
    order = _order(order_id, provider_id)
    workflow = getattr(order, "workflow", None)
    if workflow and workflow.assigned_to_id != actor.pk:
        raise PermissionDenied
    identity, previous = receipt(actor, key, action, order_id, provider_id, version, confirmed, scheduled_at,
                                 study_id, body_site, findings, impression, reason, withdrawal_kind)
    if previous:
        return previous.order
    check_version(version, order.version)
    if confirmed is not True or order.status != "signed":
        raise ValidationError("Confirm an available fictional action on a signed order.")
    if action == "imaging_assign" and workflow is None:
        workflow = ExamWorkflow.objects.create(order=order, assigned_to=actor)
        details = {"state": workflow.status}
    elif workflow is None:
        raise PermissionDenied
    elif action in REPORT_ACTIONS:
        report = _report_command(order, workflow, actor, action, findings, impression, reason, withdrawal_kind)
        details = {"revision": report.revision, "publication": report.status}
    else:
        details = _exam_command(order, workflow, action, scheduled_at, study_id, body_site)
    order.version += 1
    order.save(update_fields=["version"])
    record(actor, action, identity, order=order, order_version=order.version, **details)
    return order


def _exam_command(order, workflow, action, scheduled_at, study_id, body_site):
    now = timezone.now()
    before = workflow.status
    if action == "imaging_staff_schedule" and before == "assigned":
        schedule(order, scheduled_at)
        return {"state": before, "scheduled_at": scheduled_at.isoformat()}
    if action == "imaging_exam_start" and before == "assigned" and hasattr(order, "exam"):
        workflow.status, workflow.started_at = "started", now
    elif action == "imaging_exam_perform" and before == "started":
        if not isinstance(study_id, str) or not re.fullmatch(r"SYN-[A-Z0-9-]{1,36}", study_id):
            raise ValidationError("Enter a fictional study identifier beginning with SYN-.")
        workflow.status, workflow.performed_at = "performed", now
        workflow.study_id = study_id
        workflow.body_site = text_value(body_site, 100, "a fictional body site")
    elif action == "imaging_exam_complete" and before == "performed":
        workflow.status, workflow.completed_at = "completed", now
    else:
        raise ValidationError("This examination action is unavailable in the current state.")
    workflow.validate_constraints()
    workflow.save()
    return {"previous_state": before, "state": workflow.status, "study": workflow.study_id}


def _report_command(order, workflow, actor, action, findings, impression, reason, withdrawal_kind):
    latest = order.reports.first()
    draft = order.reports.filter(status="draft").first()
    current = current_report(order)
    state = current.status if current else None
    payload = {"order": order, "author": actor, "revision": latest.revision + 1 if latest else 1}
    if action == "imaging_report_draft" and workflow.status in ("performed", "completed") and state in (None, "preliminary"):
        payload.update(status="draft", based_on=latest)
    elif action == "imaging_preliminary" and draft and state is None and workflow.status in ("performed", "completed"):
        payload.update(status="preliminary", based_on=draft, published_at=timezone.now())
        findings, impression = draft.findings, draft.impression
    elif action == "imaging_final" and draft and state in (None, "preliminary") and workflow.status == "completed":
        payload.update(status="final", based_on=draft, published_at=timezone.now())
        findings, impression = draft.findings, draft.impression
    elif action == "imaging_correct" and state in ("final", "corrected"):
        payload.update(status="corrected", based_on=current, published_at=timezone.now(),
                       reason=text_value(reason, 240, "a correction reason"))
    elif action == "imaging_withdraw" and state in ("preliminary", "final", "corrected"):
        if withdrawal_kind not in dict(ImagingReport.WITHDRAWALS):
            raise ValidationError("Choose a withdrawal category.")
        return ImagingReport.objects.create(**payload, status="withdrawn", based_on=current, published_at=timezone.now(),
                                            withdrawal_kind=withdrawal_kind,
                                            reason=text_value(reason, 240, "a withdrawal reason"))
    else:
        raise ValidationError("This report action is unavailable in the current state.")
    return ImagingReport.objects.create(**payload, findings=text_value(findings, 4000, "fictional findings"),
                                        impression=text_value(impression, 2000, "a fictional impression"))


@command_transaction
def acknowledge(actor, order_id, provider_id, report_id, version, key, confirmed):
    if not can_write(actor, provider_id):
        raise PermissionDenied
    order = _order(order_id, provider_id)
    action = "imaging_acknowledge"
    identity, previous = receipt(actor, key, action, order_id, provider_id, report_id, version, confirmed)
    if previous:
        return previous.order
    check_version(version, order.version)
    report = current_report(order)
    if (confirmed is not True or order.status != "signed" or report is None
            or report.pk != report_id or report.status not in ("final", "corrected")):
        raise ValidationError("Confirm review of the current final report revision.")
    if hasattr(report, "review"):
        raise ValidationError("This report revision has already been acknowledged.")
    ImagingReview.objects.create(report=report, physician=actor)
    order.version += 1
    order.save(update_fields=["version"])
    record(actor, action, identity, order=order, revision=report.revision, order_version=order.version)
    return order
