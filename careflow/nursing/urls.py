from django.urls import path
from . import views

urlpatterns = [
    path("nursing/", views.workspace, name="nursing_workspace"),
    path("patients/<int:patient_id>/nursing/flowsheet/", views.flowsheet, name="nursing_flowsheet"),
    path("patients/<int:patient_id>/nursing/appointments/<int:appointment_id>/", views.appointment_documentation, name="nursing_appointment"),
    path("patients/<int:patient_id>/nursing/appointments/<int:appointment_id>/<str:kind>/new/", views.record_edit, name="nursing_create"),
    path("patients/<int:patient_id>/nursing/appointments/<int:appointment_id>/<str:kind>/<int:record_id>/", views.record_detail, name="nursing_record"),
    path("patients/<int:patient_id>/nursing/appointments/<int:appointment_id>/<str:kind>/<int:record_id>/edit/", views.record_edit, name="nursing_edit"),
]
