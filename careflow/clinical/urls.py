from django.urls import path
from . import views

urlpatterns = [
    path("physician/", views.workspace, name="physician_workspace"),
    path("patients/<int:patient_id>/chart/", views.chart, name="patient_chart"),
    path("appointments/<int:appointment_id>/start/", views.encounter_start, name="encounter_start"),
    path("patients/<int:patient_id>/encounters/<int:encounter_id>/", views.encounter_detail, name="encounter_detail"),
    path("patients/<int:patient_id>/encounters/<int:encounter_id>/complete/", views.encounter_complete, name="encounter_complete"),
    path("patients/<int:patient_id>/encounters/<int:encounter_id>/note/", views.note_edit, name="note_edit"),
    path("patients/<int:patient_id>/encounters/<int:encounter_id>/notes/<int:note_id>/sign/", views.note_sign, name="note_sign"),
]
