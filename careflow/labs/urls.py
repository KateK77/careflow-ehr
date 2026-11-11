from django.urls import path
from . import views

urlpatterns = [
    path("lab/catalog/", views.catalog_list, name="lab_catalog"),
    path("lab/catalog/new/", views.catalog_create, name="lab_catalog_create"),
    path("lab/catalog/<int:catalog_id>/activate/", views.catalog_toggle, {"active": True}, name="lab_catalog_activate"),
    path("lab/catalog/<int:catalog_id>/deactivate/", views.catalog_toggle, {"active": False}, name="lab_catalog_deactivate"),
    path("patients/<int:patient_id>/encounters/<int:encounter_id>/lab-orders/new/", views.draft_edit, name="lab_order_create"),
    path("patients/<int:patient_id>/lab-orders/", views.order_history, name="lab_patient_orders"),
    path("patients/<int:patient_id>/encounters/<int:encounter_id>/lab-orders/", views.order_history, name="lab_encounter_orders"),
    path("lab/orders/<uuid:order_id>/", views.order_detail, name="lab_order_detail"),
    path("lab/orders/<uuid:order_id>/edit/", views.draft_edit, name="lab_order_edit"),
    path("lab/orders/<uuid:order_id>/submit/", views.order_submit, name="lab_order_submit"),
    path("lab/orders/<uuid:order_id>/cancel/", views.order_cancel, name="lab_order_cancel"),
]
