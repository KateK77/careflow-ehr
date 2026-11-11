from django.urls import path
from . import views

urlpatterns = [
    path("mar/", views.worklist, name="mar_worklist"),
    path("patients/<int:patient_id>/mar/", views.worklist, name="mar_patient"),
    path("mar/tasks/<int:receipt_id>/", views.detail, name="mar_detail"),
    path("patients/<int:patient_id>/encounters/<int:encounter_id>/mar/<int:receipt_id>/record/",
         views.administer, name="mar_administer"),
]
