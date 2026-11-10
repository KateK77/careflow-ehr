"""Append-only responsibility, review and report-history commands."""
import copy
from django.contrib.auth import get_user_model
from django.core import signing
from django.core.exceptions import PermissionDenied,ValidationError
from django.db import transaction
from django.db.models import Q,Max
from django.utils import timezone
from careflow.scheduling.services import _lock_providers
from .access import is_lab,lab_roles
from .models import LabOrder,LabResult,LabReviewAssignment,LabResultReview,LabEvent
from .payloads import withdrawal_payload
from .processing import text
from .services import busy,LabConflict,_key,_fingerprint,_replay,_current,_snapshot,_event


def physician_eligible(user_id):
    return get_user_model().objects.filter(pk=user_id,is_active=True,groups__name='Physician').exists()


def explicit_permission(actor,code):
    return get_user_model().objects.filter(Q(user_permissions__content_type__app_label='labs',user_permissions__codename=code)|Q(groups__permissions__content_type__app_label='labs',groups__permissions__codename=code),pk=actor.pk,is_active=True).exists()


def initial_assignment(order,actor):
    return LabReviewAssignment.objects.create(order=order,sequence=1,physician_id=order.ordering_physician_id,assigned_by=actor,reason='Original ordering physician at submission.',source='initial_submission')


def current_reviewed(order):
    return bool(order.current_publication_id and order.current_review_assignment_id and LabResultReview.objects.filter(publication_id=order.current_publication_id,review_assignment_id=order.current_review_assignment_id).exists())


def quarantined(order):
    return order.status=='withdrawn' and order.current_publication and order.current_publication.reason_code=='context_error'


def can_inspect(actor,order):
    return (is_lab(actor) and order.assigned_lab_staff_id==actor.pk) or ('Administrator' in lab_roles(actor) and explicit_permission(actor,'view_quarantined_report'))


def authorized(actor,order,action):
    if action=='reassign':
        if 'Administrator' not in lab_roles(actor) or not explicit_permission(actor,'reassign_review_responsibility'): raise PermissionDenied
    elif action=='acknowledge':
        if not order.current_review_assignment_id or order.current_review_assignment.physician_id!=actor.pk or not physician_eligible(actor.pk): raise PermissionDenied
    elif action in {'correct','withdraw'}:
        if not is_lab(actor) or order.assigned_lab_staff_id!=actor.pk: raise PermissionDenied
    else: raise PermissionDenied


def review_token(actor,order,action,data):
    return signing.dumps({'actor':actor.pk,'order':str(order.public_id),'version':order.version,'publication':order.current_publication_id,'assignment':order.current_review_assignment_id,'action':action,'data':data},salt='lab-review-command')


def verify_token(actor,order,action,data,token):
    try:
        if signing.loads(token,salt='lab-review-command',max_age=600)!=signing.loads(review_token(actor,order,action,data),salt='lab-review-command'): raise signing.BadSignature
    except signing.BadSignature: raise ValidationError('Preview the current target and explicitly confirm within ten minutes.') from None


@busy
def review_command(actor,order_id,version,command_key,action,data,confirmed,token=''):
    order=LabOrder.objects.select_related('current_review_assignment','current_publication').get(public_id=order_id)
    authorized(actor,order,action)
    if confirmed is not True or not isinstance(data,dict): raise ValidationError('Confirm synthetic information only.')
    allowed={'reassign':{'assignment_id','physician_id','reason'},'acknowledge':{'publication_id','assignment_id','comment'},'correct':{'publication_id','assignment_id','reason'},'withdraw':{'publication_id','assignment_id','reason_code','reason'}}
    if action not in allowed or set(data)-allowed[action]: raise ValidationError('Unexpected laboratory review command fields.')
    key=_key(command_key); fingerprint=_fingerprint('review_'+action,order=str(order_id),version=version,data=data)
    with transaction.atomic():
        _lock_providers([order.ordering_physician_id])
        order=LabOrder.objects.select_for_update().select_related('current_review_assignment','current_publication').get(pk=order.pk)
        authorized(actor,order,action)
        if replay:=_replay(actor,key,fingerprint): return replay
        _current(version,order.version)
        if order.status not in {'submitted','fulfilled','withdrawn'}: raise LabConflict('This laboratory order is not eligible for review operations.')
        before=_snapshot(order); result=None; assignment=None; review=None
        if action=='reassign':
            if data.get('assignment_id')!=order.current_review_assignment_id: raise LabConflict('Review responsibility changed. Reload.')
            if physician_eligible(order.current_review_assignment.physician_id): raise LabConflict('The current responsible physician remains eligible; replacement is not permitted by this minimal policy.')
            target=data.get('physician_id')
            if not physician_eligible(target): raise ValidationError('Choose an active Physician.')
            reason=text(data,'reason'); verify_token(actor,order,action,data,token)
            assignment=LabReviewAssignment.objects.create(order=order,sequence=order.current_review_assignment.sequence+1,physician_id=target,assigned_by=actor,reason=reason,source='manual_reassignment',supersedes=order.current_review_assignment)
            order.current_review_assignment=assignment
        elif action=='acknowledge':
            if data.get('publication_id')!=order.current_publication_id or data.get('assignment_id')!=order.current_review_assignment_id or order.status not in {'fulfilled','withdrawn'}: raise LabConflict('Review the current publication under the current responsibility assignment.')
            comment=data.get('comment','')
            if not isinstance(comment,str) or len(comment)>1000: raise ValidationError('Use a comment of at most 1000 characters.')
            if quarantined(order) and comment: raise ValidationError('Context-error notice acknowledgement permits no free-text comment.')
            if current_reviewed(order): raise LabConflict('This publication has already been acknowledged under this assignment.')
            review=LabResultReview.objects.create(publication=order.current_publication,review_assignment=order.current_review_assignment,reviewer=actor,review_kind='withdrawal_notice' if order.status=='withdrawn' else 'result_review',comment=comment)
            result=order.current_publication; assignment=order.current_review_assignment
        else:
            if order.status!='fulfilled' or order.current_publication.status not in {'final','corrected'} or data.get('publication_id')!=order.current_publication_id: raise LabConflict('Target the current usable report on a fulfilled order.')
            if order.results.filter(status='draft').exists(): raise LabConflict('Explicitly abandon the active correction draft first.')
            reason=text(data,'reason'); predecessor=order.current_publication
            revision=(order.results.aggregate(n=Max('revision'))['n'] or 0)+1
            if action=='correct':
                result=LabResult.objects.create(order=order,specimen=predecessor.specimen,revision=revision,payload=copy.deepcopy(predecessor.payload),supersedes=predecessor,entered_by=actor,edited_by=actor,performed_at=predecessor.performed_at,reason=reason)
            else:
                code=data.get('reason_code')
                if code not in {'report_error','context_error'}: raise ValidationError('Select report error or context error.')
                verify_token(actor,order,action,data,token)
                result=LabResult(order=order,specimen=predecessor.specimen,revision=revision,status='withdrawn',publication_kind='withdrawal',payload=withdrawal_payload(order,predecessor,code,reason),supersedes=predecessor,entered_by=actor,edited_by=actor,finalized_by=actor,published_at=timezone.now(),reason_code=code,reason=reason)
                result.full_clean(); result.save(); order.current_publication=result; order.status='withdrawn'
        order.version+=1; order.full_clean(); order.save()
        extra={'review_metadata':{'assignment':assignment.pk if assignment else order.current_review_assignment_id,'publication':result.pk if result else order.current_publication_id,'review':review.pk if review else None},'operation_reason':data.get('reason','')}
        # These immutable event records contain metadata only; quarantined values are never serialized by clinical routes.
        return _event(actor,key,fingerprint,'lab_'+action,order,before,result=result,extra=extra,review_assignment=assignment,review=review)
