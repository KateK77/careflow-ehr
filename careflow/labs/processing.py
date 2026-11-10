"""Serialized synthetic specimen and report commands. All writes share original-provider locking."""
import copy
from datetime import datetime
from django.core import signing
from django.core.exceptions import PermissionDenied, ValidationError
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Max
from django.utils import timezone
from .access import is_lab, lab_roles
from .models import LabOrder, LabSpecimen, LabResult, LabEvent
from .payloads import envelope, validate_payload
from .services import busy, LabConflict, _current, _key, _fingerprint, _replay, _snapshot, _event
from careflow.scheduling.services import _lock_providers


def authorized(actor,order,action):
    roles=lab_roles(actor)
    if action=='assign':
        if 'Administrator' not in roles: raise PermissionDenied
    elif action=='claim':
        if not is_lab(actor) or (order.assigned_lab_staff_id and order.assigned_lab_staff_id!=actor.pk): raise PermissionDenied
    elif action in {'collect','correct_collection','recollect'}:
        if 'Nurse' not in roles: raise PermissionDenied
    elif action=='reject':
        if 'Nurse' not in roles and not (is_lab(actor) and order.assigned_lab_staff_id==actor.pk): raise PermissionDenied
    elif not (is_lab(actor) and order.assigned_lab_staff_id==actor.pk):
        raise PermissionDenied


def parse_time(value):
    if not isinstance(value,str): raise ValidationError('Enter an ISO timestamp with explicit timezone offset.')
    try: result=datetime.fromisoformat(value)
    except ValueError: raise ValidationError('Enter a valid ISO timestamp with timezone offset.') from None
    if timezone.is_naive(result) or result>timezone.now(): raise ValidationError('Use a non-future timestamp with an explicit timezone offset.')
    return result


def text(data,key):
    value=data.get(key,'')
    if not isinstance(value,str) or not 1<=len(value.strip())<=1000: raise ValidationError('Enter a reason of 1–1000 characters.')
    return value.strip()


def specimen_for(order,data):
    try: item=order.specimens.get(pk=data.get('specimen_id'))
    except (LabSpecimen.DoesNotExist,ValueError,TypeError): raise ValidationError('Select the current specimen for this order.') from None
    _current(data.get('specimen_version'),item.version)
    return item


def result_for(order,data):
    try: result=order.results.get(pk=data.get('result_id'))
    except (LabResult.DoesNotExist,ValueError,TypeError): raise ValidationError('Select a result draft from this order.') from None
    _current(data.get('result_version'),result.edit_version)
    if result.status!='draft': raise LabConflict('Only a current unpublished draft may be changed.')
    return result


def publication_token(actor,order,result):
    return signing.dumps({'actor':actor.pk,'order':str(order.public_id),'version':order.version,'result':result.pk,'edit_version':result.edit_version,'payload':result.payload,'performed_at':str(result.performed_at)},salt='lab-publication')


def verify_publication_token(actor,order,result,token):
    try:
        actual=signing.loads(token,salt='lab-publication',max_age=600)
        expected=signing.loads(publication_token(actor,order,result),salt='lab-publication')
        if actual!=expected: raise signing.BadSignature
    except signing.BadSignature:
        raise ValidationError('Preview the current report and explicitly confirm within ten minutes.') from None


@busy
def process(actor,order_id,version,command_key,action,data,confirmed):
    order=LabOrder.objects.get(public_id=order_id)
    authorized(actor,order,action)
    if confirmed is not True or not isinstance(data,dict): raise ValidationError('Confirm synthetic information only.')
    key=_key(command_key)
    # Preview token is ephemeral; durable replay fingerprints cover the semantic command.
    fingerprint=_fingerprint('processing_'+action,order=str(order_id),version=version,data={k:v for k,v in data.items() if k!='preview_token'})
    with transaction.atomic():
        _lock_providers([order.ordering_physician_id])
        order=LabOrder.objects.select_for_update().select_related('encounter').get(pk=order.pk)
        authorized(actor,order,action)
        if replay:=_replay(actor,key,fingerprint): return replay
        _current(version,order.version)
        if order.status!='submitted': raise LabConflict('This operation requires a submitted, unpublished order.')
        before=_snapshot(order); specimen=None; result=None
        if action in {'claim','assign'}:
            target=actor if action=='claim' else get_user_model().objects.filter(pk=data.get('assignee_id'),is_active=True,groups__name='Lab Staff').first()
            if not target: raise ValidationError('Select an active Lab Staff account.')
            if order.assigned_lab_staff_id:
                previous=get_user_model().objects.get(pk=order.assigned_lab_staff_id)
                if previous.is_active and previous.groups.filter(name='Lab Staff').exists(): raise LabConflict('An eligible laboratory assignee cannot be replaced.')
            text(data,'reason')
            order.assigned_lab_staff=target
        elif action=='recollect':
            text(data,'reason')
            if order.specimens.exclude(status='rejected').exists() or order.results.exclude(status='abandoned').exists(): raise LabConflict('Recollection requires rejection of all attempts and no active result.')
            attempt=(order.specimens.aggregate(n=Max('attempt'))['n'] or 0)+1
            specimen=LabSpecimen.objects.create(order=order,attempt=attempt,specimen_type=order.catalog_snapshot['specimen_type'],created_by=actor)
        elif action in {'collect','correct_collection','receive','reject'}:
            specimen=specimen_for(order,data)
            if action in {'collect','correct_collection'}:
                if specimen.status!=('pending' if action=='collect' else 'collected'): raise LabConflict('Collection correction is allowed only before receipt; rejected attempts are permanent.')
                if data.get('identity_confirmed') is not True or data.get('mrn')!=order.patient.mrn or data.get('dob')!=order.patient.dob.isoformat(): raise ValidationError('Confirm the correct synthetic patient using MRN and date of birth.')
                if action=='correct_collection': text(data,'reason')
                collected=parse_time(data.get('collected_at'))
                if collected<order.submitted_at: raise ValidationError('Collection cannot precede submission.')
                specimen.status='collected'; specimen.collected_at=collected; specimen.collected_by=actor
                specimen.comments=data.get('reason','')
            elif action=='receive':
                if specimen.status!='collected': raise LabConflict('Receipt requires a collected active attempt.')
                specimen.status='received'; specimen.received_at=timezone.now(); specimen.received_by=actor
                if specimen.collected_at>specimen.received_at: raise ValidationError('Receipt cannot precede collection.')
            else:
                if specimen.status not in {'collected','received'} or order.results.filter(status='draft').exists(): raise LabConflict('Reject a collected/received specimen only after explicitly abandoning any result draft.')
                if specimen.status=='received' and not (is_lab(actor) and order.assigned_lab_staff_id==actor.pk): raise PermissionDenied
                specimen.status='rejected'; specimen.rejected_at=timezone.now(); specimen.rejected_by=actor; specimen.rejection_reason=text(data,'reason')
            specimen.version+=1; specimen.full_clean(); specimen.save()
        elif action=='result_create':
            specimen=specimen_for(order,data)
            if specimen.status!='received' or order.results.filter(status='draft').exists() or order.current_publication_id: raise LabConflict('Start a draft only for the received active specimen without an existing draft/publication.')
            result=LabResult(order=order,specimen=specimen,revision=(order.results.aggregate(n=Max('revision'))['n'] or 0)+1,entered_by=actor,edited_by=actor,payload=envelope(order,specimen,[]))
            result.full_clean(); result.save()
        elif action in {'result_save','abandon','publish'}:
            result=result_for(order,data); specimen=result.specimen
            if specimen.status!='received': raise LabConflict('A received specimen is required.')
            if action=='result_save':
                components=data.get('components')
                result.payload=envelope(order,specimen,copy.deepcopy(components))
                validate_payload(order,specimen,result.payload)
                result.performed_at=parse_time(data['performed_at']) if data.get('performed_at') else None
                performed=any(c['value_kind']!='absent' for c in components)
                if performed and (not result.performed_at or result.performed_at<specimen.received_at): raise ValidationError('Performed measurements require a timestamp at or after receipt.')
                if not performed and result.performed_at: raise ValidationError('An all-not-performed or empty draft must not invent a performed time.')
                result.edited_by=actor
            elif action=='abandon':
                result.status='abandoned'; result.reason=text(data,'reason'); result.edited_by=actor
            else:
                verify_publication_token(actor,order,result,data.get('preview_token',''))
                validate_payload(order,specimen,result.payload,complete=True)
                performed=any(c['value_kind']!='absent' for c in result.payload['components'])
                if performed and (not result.performed_at or not specimen.received_at<=result.performed_at<=timezone.now()): raise ValidationError('Valid performed time is required for performed measurements.')
                if not performed and result.performed_at: raise ValidationError('Not-performed reports have no performed time.')
                result.status='final'; result.finalized_by=actor; result.published_at=timezone.now()
            result.edit_version+=1; result.full_clean(); result.save()
            if action=='publish': order.status='fulfilled'; order.current_publication=result; order.fulfilled_at=result.published_at
        else: raise ValidationError('Unknown laboratory command.')
        order.version+=1; order.full_clean(); order.save()
        extra={'operation_reason':data.get('reason','')}
        if result: extra['result_metadata']={'id':result.pk,'revision':result.revision,'status':result.status,'edit_version':result.edit_version}
        return _event(actor,key,fingerprint,'lab_'+action,order,before,specimen,result,extra)
