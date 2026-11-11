from django.urls import path
from . import views

urlpatterns = [
    path("portal/login/", views.PortalLogin.as_view(), name="portal_login"),
    path("portal/logout/", views.PortalLogout.as_view(), name="portal_logout"),
    path("portal/", views.dashboard, name="portal_home"),
    path("portal/appointments/", views.records, {"kind": "appointments"}, name="portal_appointments"),
    path("portal/visits/", views.records, {"kind": "visits"}, name="portal_visits"),
    path("portal/medications/", views.records, {"kind": "medications"}, name="portal_medications"),
    path("portal/results/", views.results, name="portal_results"),
    path("portal/results/<int:result_id>/", views.results, name="portal_result"),
    path("app/portal/releases/", views.releases, name="portal_releases"),
]
