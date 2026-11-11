from django import forms
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods, require_safe

from careflow.clinical.access import can_write
from careflow.patients.access import roles_for

from .access import orders_for
from .models import ImagingReport
from .views import CommandForm, order_history, submit
from .workflow import acknowledge, available_orders, current_report, radiology_command, workspace_orders


WORKFLOW_ACTIONS = {
    "imaging_assign": "Assign to me", "imaging_staff_schedule": "Schedule or reschedule",
    "imaging_exam_start": "Start examination", "imaging_exam_perform": "Record examination performed",
    "imaging_exam_complete": "Complete examination", "imaging_report_draft": "Save draft revision",
    "imaging_preliminary": "Publish preliminary report", "imaging_final": "Publish final report",
    "imaging_correct": "Publish correction", "imaging_withdraw": "Withdraw report",
    "imaging_acknowledge": "Report acknowledged",
}


class ExamForm(CommandForm):
    action = forms.ChoiceField(choices=WORKFLOW_ACTIONS.items())
    scheduled_at = forms.DateTimeField(required=False, label="Clinic-local examination time",
                                      widget=forms.DateTimeInput(attrs={"type": "datetime-local"}))
    study_id = forms.CharField(max_length=40, required=False, label="Fictional SYN- study identifier")
    body_site = forms.CharField(max_length=100, required=False, label="Fictional body site")
    findings = forms.CharField(max_length=4000, required=False, widget=forms.Textarea(attrs={"rows": 4}))
    impression = forms.CharField(max_length=2000, required=False, widget=forms.Textarea(attrs={"rows": 3}))
    reason = forms.CharField(max_length=240, required=False, label="Correction or withdrawal reason")
    withdrawal_kind = forms.ChoiceField(choices=[("", "None"), *ImagingReport.WITHDRAWALS],
                                        required=False, label="Withdrawal category")
    confirmed = forms.BooleanField(label="Confirm fictional radiology action")

    def __init__(self, *args, allowed, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            self.fields["action"].choices = [(key, WORKFLOW_ACTIONS[key]) for key in allowed]


class ReviewForm(CommandForm):
    report_id = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    confirmed = forms.BooleanField(label="Confirm review of this published revision")


def _actions(order, current):
    if order.status != "signed":
        return []
    workflow = getattr(order, "workflow", None)
    if workflow is None:
        return ["imaging_assign"]
    if workflow.status == "assigned":
        return ["imaging_staff_schedule"] + (["imaging_exam_start"] if hasattr(order, "exam") else [])
    if workflow.status == "started":
        return ["imaging_exam_perform"]
    allowed = ["imaging_exam_complete"] if workflow.status == "performed" else []
    state = current.status if current else None
    if state in (None, "preliminary"):
        allowed.append("imaging_report_draft")
        if order.reports.filter(status="draft").exists():
            if state is None:
                allowed.append("imaging_preliminary")
            if workflow.status == "completed":
                allowed.append("imaging_final")
    if state in ("final", "corrected"):
        allowed.append("imaging_correct")
    if state in ("preliminary", "final", "corrected"):
        allowed.append("imaging_withdraw")
    return allowed


@never_cache
@require_safe
def worklist(request):
    assigned = workspace_orders(request.user)
    return render(request, "imaging/workspace.html", {
        "assigned": assigned, "available": available_orders(request.user),
    })


@never_cache
@require_http_methods(["GET", "POST"])
def exam_detail(request, order_id):
    owned = workspace_orders(request.user)
    available = available_orders(request.user)
    order = owned.filter(pk=order_id).first() or get_object_or_404(available, pk=order_id)
    assigned = hasattr(order, "workflow")
    current = current_report(order) if assigned else None
    quarantine = bool(current and current.withdrawal_kind == "context_error")
    draft = order.reports.filter(status="draft").first() if assigned and not quarantine else None
    starting_report = current if current and current.status in ("final", "corrected") else draft
    form = ExamForm(request.POST if request.method == "POST" else None, allowed=_actions(order, current), initial={
        "version": order.version, "findings": starting_report.findings if starting_report else "",
        "impression": starting_report.impression if starting_report else "",
    })
    if request.method == "POST":
        def save(data):
            return radiology_command(request.user, order.pk, order.encounter.physician_id, **data)
        if submit(form, save):
            return redirect("imaging_exam", order.pk)
    return render(request, "imaging/exam.html", {
        "order": order, "assigned": assigned, "form": form, "quarantine": quarantine,
        "reports": order.reports.select_related("author", "review") if assigned else [],
        "history": order_history(order) if assigned else [],
    }, status=400 if form.errors else 200)


@never_cache
@require_http_methods(["GET", "POST"])
def report_detail(request, order_id):
    order = get_object_or_404(orders_for(request.user), pk=order_id, signed_at__isnull=False)
    physician = can_write(request.user, order.encounter.physician_id)
    nurse = "Nurse" in roles_for(request.user)
    if not physician and not nurse:
        raise PermissionDenied
    current = current_report(order)
    reviewable = bool(current and current.status in ("final", "corrected"))
    can_review = physician and reviewable and not hasattr(current, "review")
    form = ReviewForm(request.POST if request.method == "POST" else None, initial={
        "version": order.version, "report_id": current.pk if current else None,
    })
    if request.method == "POST":
        if not physician:
            raise PermissionDenied
        def save(data):
            return acknowledge(request.user, order.pk, order.encounter.physician_id, **data)
        if submit(form, save):
            return redirect("imaging_report", order.pk)
    visible = current if reviewable or (physician and current and current.status == "preliminary") else None
    return render(request, "imaging/report.html", {
        "order": order, "visible": visible, "withdrawn": bool(current and current.status == "withdrawn"),
        "chronology": order.reports.filter(status__in=(
            ["preliminary", "final", "corrected", "withdrawn"] if physician else ["final", "corrected", "withdrawn"]
        )).select_related("author", "review"), "form": form, "can_review": can_review,
    }, status=400 if form.errors else 200)


@never_cache
@require_safe
def review_worklist(request):
    if not can_write(request.user, request.user.pk):
        raise PermissionDenied
    orders = orders_for(request.user).filter(encounter__physician=request.user,
        publication_status__in=["final", "corrected"], publication_review__isnull=True)
    return render(request, "imaging/review_worklist.html", {"orders": orders})
