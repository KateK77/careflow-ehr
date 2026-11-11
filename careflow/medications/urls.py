from django.urls import path
from . import pharmacy_views, views

urlpatterns = [
    path("pharmacy/", pharmacy_views.worklist, name="pharmacy_worklist"),
    path("pharmacy/orders/<uuid:order_id>/", pharmacy_views.pharmacy_detail, name="pharmacy_detail"),
    path("pharmacy/orders/<uuid:order_id>/claim/", pharmacy_views.action, {"action": "claim"}, name="pharmacy_claim"),
    path("pharmacy/orders/<uuid:order_id>/<str:action>/", pharmacy_views.action, name="pharmacy_action"),
    path("medication-orders/<uuid:order_id>/clarification/", pharmacy_views.respond, name="pharmacy_respond"),
    path("medications/catalog/", views.catalog, name="med_catalog"),
    path("medications/catalog/new/", views.catalog_create, name="med_catalog_create"),
    path("medications/catalog/<int:catalog_id>/activate/", views.catalog_activation, {"active": True}, name="med_activate"),
    path("medications/catalog/<int:catalog_id>/retire/", views.catalog_activation, {"active": False}, name="med_retire"),
    path("patients/<int:patient_id>/medication-orders/", views.history, name="med_history"),
    path("patients/<int:patient_id>/encounters/<int:encounter_id>/medication-orders/", views.history, name="med_encounter_history"),
    path("patients/<int:patient_id>/encounters/<int:encounter_id>/medication-orders/new/", views.compose, name="med_create"),
    path("patients/<int:patient_id>/encounters/<int:encounter_id>/medication-orders/<uuid:order_id>/edit/", views.compose, name="med_edit"),
    path("medication-orders/<uuid:order_id>/", views.detail, name="med_detail"),
    path("medication-orders/<uuid:order_id>/sign/", views.transition, {"action": "sign"}, name="med_sign"),
    path("medication-orders/<uuid:order_id>/cancel/", views.transition, {"action": "cancel"}, name="med_cancel"),
]
