from django.urls import path

from . import claim_views, views

urlpatterns = [
    path("app/billing/", views.worklist, name="billing_worklist"),
    path("app/billing/catalog/", views.catalog, name="billing_catalog"),
    path("app/billing/coverage/", views.coverage, name="billing_coverage"),
    path("app/billing/encounters/<int:encounter_id>/", views.encounter, name="billing_encounter"),
    path("app/billing/claims/", claim_views.worklist, name="billing_claims"),
    path("app/billing/claims/new/<int:statement_id>/", claim_views.new_claim, name="billing_claim_new"),
    path("app/billing/claims/<int:claim_id>/", claim_views.claim_detail, name="billing_claim"),
    path("app/billing/payments/<int:statement_id>/", claim_views.payments, name="billing_payments"),
    path("portal/billing/statements/<int:statement_id>/payments/", claim_views.portal_payments, name="portal_payments"),
    path("portal/billing/", views.portal_list, name="portal_billing"),
    path("portal/billing/statements/<int:statement_id>/", views.portal_detail, name="portal_statement"),
]
