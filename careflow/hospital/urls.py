from django.urls import path
from . import views

urlpatterns = [
    path("inpatient/", views.dashboard, name="hospital_dashboard"),
    path("inpatient/capacity/", views.capacity, name="hospital_capacity"),
    path("inpatient/facilities/", views.facilities, name="hospital_facilities"),
    path("inpatient/facilities/<str:kind>/", views.facilities, name="hospital_facility"),
    path("inpatient/admissions/", views.admissions, name="hospital_admissions"),
    path("patients/<int:patient_id>/inpatient/admissions/<int:request_id>/", views.admission, name="hospital_admission"),
    path("patients/<int:patient_id>/inpatient/stays/<int:stay_id>/", views.stay, name="hospital_stay"),
]
