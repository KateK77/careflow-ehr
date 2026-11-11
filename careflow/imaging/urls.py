from django.urls import path

from . import views

urlpatterns = [
    path("imaging/catalog/", views.catalog, name="imaging_catalog"),
    path("imaging/orders/<int:order_id>/", views.order_detail, name="imaging_order"),
    path("patients/<int:patient_id>/encounters/<int:encounter_id>/imaging/new/", views.order_new, name="imaging_order_new"),
    path("patients/<int:patient_id>/imaging/", views.patient_orders, name="imaging_patient"),
]
