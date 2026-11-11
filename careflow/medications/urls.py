from django.urls import path
from . import views

urlpatterns = [
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
