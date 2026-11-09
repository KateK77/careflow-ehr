from django.urls import path

from . import views


urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
    path("patients/", views.patient_list, name="patient_list"),
    path("patients/new/", views.patient_edit, name="patient_create"),
    path("patients/<int:pk>/", views.patient_detail, name="patient_detail"),
    path("patients/<int:pk>/edit/", views.patient_edit, name="patient_edit"),
]
