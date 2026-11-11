import uuid
from django import forms
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied,ValidationError
from django.core.paginator import Paginator
from django.shortcuts import render,redirect,get_object_or_404
from django.views.decorators.http import require_safe,require_http_methods
from careflow.patients.models import AuditEvent
from .access import orders_for,publications_for,lab_roles,is_lab
from .forms import CommandForm
from .models import LabOrder
from .processing_views import lab_access
from .presentation import presentation
from .review import authorized,review_command,review_token,explicit_permission,current_reviewed,physician_eligible,quarantined
from .services import LabConflict
from .views import errors


class ReviewForm(CommandForm):
    def __init__(self,*args,action,order,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['version'].initial=order.version
        self.fields['publication_id']=forms.IntegerField(required=False,widget=forms.HiddenInput,initial=order.current_publication_id)
        self.fields['assignment_id']=forms.IntegerField(widget=forms.HiddenInput,initial=order.current_review_assignment_id)
        self.fields['preview_token']=forms.CharField(required=False,widget=forms.HiddenInput)
        if action in {'correct','withdraw','reassign'}: self.fields['reason']=forms.CharField(max_length=1000,widget=forms.Textarea(attrs={'rows':3}))
        if action=='withdraw': self.fields['reason_code']=forms.ChoiceField(choices=[('report_error','Report error'),('context_error','Patient/specimen context error — quarantine prior payloads')])
        if action=='reassign': self.fields['physician']=forms.ModelChoiceField(queryset=get_user_model().objects.filter(is_active=True,groups__name='Physician').distinct())
        if action=='acknowledge' and not quarantined(order): self.fields['comment']=forms.CharField(required=False,max_length=1000,widget=forms.Textarea(attrs={'rows':2}))

    def command_data(self):
        d={k:v for k,v in self.cleaned_data.items() if k not in {'version','command_key','synthetic_confirmed','preview_token'}}
        if 'physician' in d:d['physician_id']=d.pop('physician').pk
        # Reassignment has no report target; keep its immutable assignment target explicit.
        if 'physician_id' in d: d.pop('publication_id',None)
        return d


@require_safe
@lab_access
def results_worklist(request):
    from django.db.models import Q
    if 'Physician' not in lab_roles(request.user) and 'Administrator' not in lab_roles(request.user): raise PermissionDenied
    orders=orders_for(request.user).exclude(current_review_assignment__isnull=True)
    if 'Administrator' not in lab_roles(request.user): orders=orders.filter(current_review_assignment__physician=request.user)
    rows=[]
    for order in orders.select_related('current_review_assignment__physician','current_publication'):
        if not order.current_publication_id or not current_reviewed(order) or not physician_eligible(order.current_review_assignment.physician_id):
            rows.append({'order':order,'reviewed':current_reviewed(order),'unresolved':not physician_eligible(order.current_review_assignment.physician_id)})
    return render(request,'labs/results_worklist.html',{'page':Paginator(rows,25).get_page(request.GET.get('page'))})


@require_safe
@lab_access
def report_detail(request,order_id):
    order=get_object_or_404(publications_for(request.user),public_id=order_id)
    AuditEvent.objects.create(actor=request.user,patient=order.patient,action='lab_report_view')
    roles=lab_roles(request.user); assigned=is_lab(request.user) and order.assigned_lab_staff_id==request.user.pk
    current_assignee=bool(order.current_review_assignment_id and order.current_review_assignment.physician_id==request.user.pk and physician_eligible(request.user.pk))
    return render(request,'labs/report_detail.html',{'order':order,'patient':order.patient,**presentation(request.user,order),
        'can_process':orders_for(request.user).filter(pk=order.pk).exists(),
        'can_acknowledge':current_assignee and not current_reviewed(order),
        'can_reassign':'Administrator' in roles and explicit_permission(request.user,'reassign_review_responsibility') and not physician_eligible(order.current_review_assignment.physician_id),
        'can_correct':assigned and order.status=='fulfilled' and not order.results.filter(status='draft').exists(),
        'can_withdraw':assigned and order.status=='fulfilled' and not order.results.filter(status='draft').exists()})


REVIEW_ACTION_LABELS = {
    "acknowledge": ("Acknowledge laboratory publication", "", "Confirm acknowledgement"),
    "correct": ("Create correction draft", "", "Create correction draft"),
    "reassign": ("Reassign review responsibility", "Preview reassignment", "Confirm reassignment"),
    "withdraw": ("Withdraw laboratory report", "Preview withdrawal", "Confirm withdrawal"),
}


@require_http_methods(['GET','POST'])
@lab_access
def command(request,order_id,action):
    if action=='acknowledge': order=get_object_or_404(publications_for(request.user),public_id=order_id)
    else: order=get_object_or_404(orders_for(request.user),public_id=order_id)
    authorized(request.user,order,action)
    form=ReviewForm(request.POST if request.method=='POST' else None,action=action,order=order)
    status=200; preview=False; token=''
    if request.method=='POST':
        status=400
        if form.is_valid():
            d=form.cleaned_data; data=form.command_data()
            try:
                if action in {'withdraw','reassign'} and request.POST.get('step')=='preview':
                    if d['version']!=order.version: raise LabConflict('This order changed. Reload before preview.')
                    token=review_token(request.user,order,action,data); preview=True; status=200
                else:
                    outcome=review_command(request.user,order.public_id,d['version'],d['command_key'],action,data,d['synthetic_confirmed'],d['preview_token'])
                    messages.success(request,'Command already processed.' if outcome.replayed else 'Laboratory review/history action recorded.')
                    return redirect('lab_report_detail' if outcome.record.current_publication_id else 'lab_processing_detail',order_id=order.public_id)
            except ValidationError as error:
                errors(form,error); status=409 if isinstance(error,LabConflict) else 400
    title, preview_label, confirm_label = REVIEW_ACTION_LABELS[action]
    return render(request,'labs/review_form.html',{'order':order,'form':form,'action':action,'preview':preview,'token':token,'title':title,'preview_label':preview_label,'confirm_label':confirm_label,'needs_preview':action in {'withdraw','reassign'},**presentation(request.user,order)},status=status)
