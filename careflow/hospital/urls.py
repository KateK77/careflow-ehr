from django.urls import path
from . import ed_views, views

urlpatterns = [
    path("ed/", ed_views.board, name="ed_board"),
    path("patients/<int:patient_id>/ed/visits/<int:visit_id>/", ed_views.visit_detail, name="ed_visit"),
    path("inpatient/", views.dashboard, name="hospital_dashboard"),
    path("inpatient/capacity/", views.capacity, name="hospital_capacity"),
    path("inpatient/facilities/", views.facilities, name="hospital_facilities"),
    path("inpatient/facilities/<str:kind>/", views.facilities, name="hospital_facility"),
    path("inpatient/admissions/", views.admissions, name="hospital_admissions"),
    path("patients/<int:patient_id>/inpatient/admissions/<int:request_id>/", views.admission, name="hospital_admission"),
    path("patients/<int:patient_id>/inpatient/stays/<int:stay_id>/", views.stay, name="hospital_stay"),
]
