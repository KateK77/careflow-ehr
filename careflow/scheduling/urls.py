from django.urls import path

from . import views


urlpatterns = [
    path("schedule/", views.schedule, name="schedule"),
    path("check-in/", views.checkin_worklist, name="checkin_worklist"),
    path("appointments/new/", views.appointment_edit, name="appointment_create"),
    path("appointments/<int:pk>/", views.appointment_detail, name="appointment_detail"),
    path("appointments/<int:pk>/edit/", views.appointment_edit, name="appointment_edit"),
    path("appointments/<int:pk>/transition/", views.appointment_transition, name="appointment_transition"),
]
