"""Bounded laboratory-only UI, separate from chart role whitelists."""
import json
from functools import wraps
from django import forms
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods, require_safe
from django.utils import timezone
from .access import lab_roles, orders_for, is_lab
from .models import LabOrder, LabResult
from .forms import CommandForm
from .processing import authorized, process, publication_token
from .services import LabConflict
from .views import errors
from careflow.patients.models import AuditEvent


def lab_access(view):
    @wraps(view)
    def guard(request,*args,**kwargs):
        if not set(lab_roles(request.user)) & {'Administrator','Physician','Nurse','Lab Staff'}:
            if not request.user.is_authenticated: return redirect_to_login(request.get_full_path())
            raise PermissionDenied
        return view(request,*args,**kwargs)
    return guard


class ProcessingForm(CommandForm):
    def __init__(self,*args,action,order,**kwargs):
        super().__init__(*args,**kwargs)
        active=order.specimens.exclude(status='rejected').first()
        draft=order.results.filter(status='draft').first()
        self.fields['version'].initial=order.version
        if action in {'collect','correct_collection','receive','reject','result_create'}:
            self.fields['specimen_id']=forms.IntegerField(widget=forms.HiddenInput,initial=active.pk if active else 0)
            self.fields['specimen_version']=forms.IntegerField(widget=forms.HiddenInput,initial=active.version if active else 0)
        if action in {'result_save','publish','abandon'}:
            self.fields['result_id']=forms.IntegerField(widget=forms.HiddenInput,initial=draft.pk if draft else 0)
            self.fields['result_version']=forms.IntegerField(widget=forms.HiddenInput,initial=draft.edit_version if draft else 0)
        if action in {'assign','claim','correct_collection','reject','recollect','abandon'}:
            self.fields['reason']=forms.CharField(max_length=1000,widget=forms.Textarea(attrs={'rows':3}))
        if action=='receive': self.fields['accession']=forms.UUIDField(label='Confirm specimen accession')
        if action=='assign':
            self.fields['assignee']=forms.ModelChoiceField(queryset=get_user_model().objects.filter(is_active=True,groups__name='Lab Staff').distinct())
        if action in {'collect','correct_collection'}:
            self.fields['mrn']=forms.CharField(label='Confirm patient MRN',max_length=32)
            self.fields['dob']=forms.DateField(label='Confirm patient date of birth',widget=forms.DateInput(attrs={'type':'date'}))
            self.fields['identity_confirmed']=forms.BooleanField(label='I verified both synthetic patient identifiers against this order.')
            self.fields['collected_at']=forms.CharField(label='Collected at (ISO timestamp with timezone offset)',initial=lambda:timezone.now().isoformat(),max_length=50)
        if action=='result_save':
            initial=draft.payload['components'] if draft else []
            if not initial:
                initial=[{'code':d['code'],'value_kind':d['type'],'value':'','unit':d['unit']} if d['type']=='numeric' else {'code':d['code'],'value_kind':'coded','value':''} for d in order.catalog_snapshot['components']]
            self.fields['components']=forms.JSONField(initial=initial,widget=forms.Textarea(attrs={'rows':12}),help_text='Strict typed JSON. Numeric values are decimal strings with exact demo units. Use value_kind absent, absence_reason not_performed and absence_explanation for an unperformed component. Required components must be accounted for before publication.')
            self.fields['performed_at']=forms.CharField(required=False,max_length=50,initial=draft.performed_at.isoformat() if draft and draft.performed_at else '',help_text='ISO timestamp with timezone offset; receipt ≤ performed ≤ now. Leave blank for all-not-performed reports.')
        if action=='publish': self.fields['preview_token']=forms.CharField(required=False,widget=forms.HiddenInput)

    def command_data(self):
        d={k:v for k,v in self.cleaned_data.items() if k not in {'command_key','version','synthetic_confirmed'}}
        if 'assignee' in d: d['assignee_id']=d.pop('assignee').pk
        if 'accession' in d: d['accession']=str(d['accession'])
        if 'dob' in d: d['dob']=d['dob'].isoformat()
        return d


@require_safe
@lab_access
def worklist(request):
    roles=lab_roles(request.user)
    records=orders_for(request.user).exclude(status='draft')
    # Unassigned requisitions expose only accession/order identity and panel until explicit claim.
    unassigned=LabOrder.objects.filter(status='submitted',assigned_lab_staff__isnull=True).only('public_id','version','catalog_snapshot') if is_lab(request.user) else LabOrder.objects.none()
    AuditEvent.objects.create(actor=request.user,action='lab_worklist_view')
    return render(request,'labs/worklist.html',{'page':Paginator(records,25).get_page(request.GET.get('page')),'unassigned':unassigned[:50],'nurse':'Nurse' in roles,'lab':is_lab(request.user),'admin':'Administrator' in roles})


@require_safe
@lab_access
def processing_detail(request,order_id):
    order=get_object_or_404(orders_for(request.user),public_id=order_id)
    roles=lab_roles(request.user); active=order.specimens.exclude(status='rejected').first(); draft=order.results.filter(status='draft').first()
    actions=[]
    if order.status=='submitted':
        if 'Administrator' in roles: actions.append(('assign','Assign laboratory staff'))
        if 'Nurse' in roles:
            if not active: actions.append(('recollect','Prepare recollection'))
            elif active.status=='pending': actions.append(('collect','Collect specimen'))
            elif active.status=='collected': actions.extend([('correct_collection','Correct collection'),('reject','Reject specimen')])
        if is_lab(request.user) and order.assigned_lab_staff_id==request.user.pk:
            if active and active.status=='collected': actions.extend([('receive','Receive specimen'),('reject','Reject specimen')])
            elif active and active.status=='received':
                actions.extend([('result_save','Edit result draft'),('publish','Preview and finalize'),('abandon','Abandon result draft')] if draft else [('result_create','Start result draft'),('reject','Reject specimen')])
    AuditEvent.objects.create(actor=request.user,patient=order.patient,action='lab_processing_view')
    return render(request,'labs/processing_detail.html',{'order':order,'patient':order.patient,'actions':actions,'specimens':order.specimens.select_related('collected_by','received_by','rejected_by'),'results':order.results.select_related('entered_by','finalized_by'),'events':order.events.select_related('audit__actor')[:100]})


@require_http_methods(['GET','POST'])
@lab_access
def command(request,order_id,action):
    if action=='claim': order=get_object_or_404(LabOrder,status='submitted',public_id=order_id)
    else: order=get_object_or_404(orders_for(request.user),public_id=order_id)
    authorized(request.user,order,action)
    if action not in {'assign','claim','collect','correct_collection','reject','receive','recollect','result_create','result_save','abandon','publish'}: raise PermissionDenied
    form=ProcessingForm(request.POST if request.method=='POST' else None,action=action,order=order)
    status=200; preview=False; token=''; draft=None
    if request.method=='POST':
        status=400
        if form.is_valid():
            d=form.cleaned_data
            try:
                if action=='publish' and request.POST.get('step')=='preview':
                    from .processing import result_for
                    from .payloads import validate_payload
                    if d['version']!=order.version: raise LabConflict('This order changed. Reload before preview.')
                    draft=result_for(order,form.command_data()); validate_payload(order,draft.specimen,draft.payload,complete=True)
                    token=publication_token(request.user,order,draft); preview=True; status=200
                else:
                    outcome=process(request.user,order.public_id,d['version'],d['command_key'],action,form.command_data(),d['synthetic_confirmed'])
                    messages.success(request,'Command already processed.' if outcome.replayed else 'Laboratory action recorded with audit history.')
                    return redirect('lab_processing_detail',order_id=order.public_id)
            except ValidationError as error:
                errors(form,error); status=409 if isinstance(error,LabConflict) else 400
    return render(request,'labs/processing_form.html',{'order':order,'form':form,'action':action,'preview':preview,'token':token,'draft':draft,'claim':action=='claim'},status=status)
