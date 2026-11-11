"""Safe projections: quarantine is applied before any value/comment reaches a template."""
from .access import is_lab,publications_for,orders_for
from .review import quarantined,can_inspect,current_reviewed,physician_eligible


def presentation(actor,order):
    restricted=bool(quarantined(order) and not can_inspect(actor,order))
    assigned=is_lab(actor) and order.assigned_lab_staff_id==actor.pk
    reports=[]
    queryset=order.results.select_related('entered_by','finalized_by','supersedes')
    if not assigned: queryset=queryset.filter(status__in=['final','corrected','withdrawn'])
    for r in queryset:
        reports.append({'id':r.pk,'revision':r.revision,'status':r.status,'status_label':r.get_status_display(),'current':r.pk==order.current_publication_id,'published_at':r.published_at,'entered_at':r.entered_at,'entered_by':r.entered_by.username,'finalizer':r.finalized_by.username if r.finalized_by_id else '',
            'payload':None if restricted else r.payload,'reason':'' if restricted else r.reason,'reason_code':r.reason_code,'performed_at':None if restricted else r.performed_at,'predecessor':r.supersedes.revision if r.supersedes_id else None})
    reviews=[]
    from .models import LabResultReview
    for r in LabResultReview.objects.filter(publication__order=order).select_related('publication','review_assignment','reviewer'):
        reviews.append({'revision':r.publication.revision,'sequence':r.review_assignment.sequence,'reviewer':r.reviewer.username,'at':r.reviewed_at,'kind':r.get_review_kind_display(),'comment':'' if restricted else r.comment})
    return {'report_rows':reports,'review_rows':reviews,'quarantine_restricted':restricted,'withdrawn':order.status=='withdrawn','reviewed':current_reviewed(order),
        'responsibility_unresolved':bool(order.current_review_assignment_id and not physician_eligible(order.current_review_assignment.physician_id))}


def chart_context(actor,patient,encounter=None):
    from django.db.models import Q
    from .models import LabOrder
    orders=LabOrder.objects.filter(Q(pk__in=publications_for(actor))|Q(pk__in=orders_for(actor).exclude(status='draft'))).filter(patient=patient).select_related('current_publication','current_review_assignment__physician')
    if encounter: orders=orders.filter(encounter=encounter)
    rows=[]
    for order in orders[:30]:
        current=order.current_publication
        rows.append({'public_id':order.public_id,'panel':order.catalog_snapshot['display_name'],'status':order.status,'revision':current.revision if current else None,'publication_status':current.status if current else 'pending','published_at':current.published_at if current else None,'reviewed':current_reviewed(order),'unresolved':not physician_eligible(order.current_review_assignment.physician_id) if order.current_review_assignment_id else True})
    return {'lab_summary':rows}
