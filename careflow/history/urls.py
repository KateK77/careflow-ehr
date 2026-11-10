from django.urls import path
from . import views

urlpatterns = [
    path("patients/<int:patient_id>/history/<str:kind>/", views.record_list, name="history_list"),
    path("patients/<int:patient_id>/history/<str:kind>/new/", views.record_edit, name="history_create"),
    path("patients/<int:patient_id>/history/<str:kind>/<int:record_id>/", views.record_detail, name="history_detail"),
    path("patients/<int:patient_id>/history/<str:kind>/<int:record_id>/edit/", views.record_edit, name="history_edit"),
    path("patients/<int:patient_id>/history/<str:kind>/<int:record_id>/review/", views.record_review, name="history_review"),
    path("patients/<int:patient_id>/allergy-assessment/", views.allergy_state_review, name="allergy_state_review"),
    path("patients/<int:patient_id>/encounters/<int:encounter_id>/diagnoses/", views.record_list, {"kind": "diagnoses"}, name="diagnosis_list"),
    path("patients/<int:patient_id>/encounters/<int:encounter_id>/diagnoses/new/", views.record_edit, {"kind": "diagnoses"}, name="diagnosis_create"),
    path("patients/<int:patient_id>/encounters/<int:encounter_id>/diagnoses/<int:record_id>/", views.record_detail, {"kind": "diagnoses"}, name="diagnosis_detail"),
    path("patients/<int:patient_id>/encounters/<int:encounter_id>/diagnoses/<int:record_id>/edit/", views.record_edit, {"kind": "diagnoses"}, name="diagnosis_edit"),
    path("patients/<int:patient_id>/encounters/<int:encounter_id>/diagnoses/<int:record_id>/review/", views.record_review, {"kind": "diagnoses"}, name="diagnosis_review"),
]
