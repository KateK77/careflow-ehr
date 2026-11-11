from django.urls import path

from . import views

urlpatterns = [
    path("app/billing/", views.worklist, name="billing_worklist"),
    path("app/billing/catalog/", views.catalog, name="billing_catalog"),
    path("app/billing/coverage/", views.coverage, name="billing_coverage"),
    path("app/billing/encounters/<int:encounter_id>/", views.encounter, name="billing_encounter"),
    path("portal/billing/", views.portal_list, name="portal_billing"),
    path("portal/billing/statements/<int:statement_id>/", views.portal_detail, name="portal_statement"),
]
