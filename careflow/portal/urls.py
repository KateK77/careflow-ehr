from django.urls import path
from . import communication_views, views

urlpatterns = [
    path("portal/login/", views.PortalLogin.as_view(), name="portal_login"),
    path("portal/logout/", views.PortalLogout.as_view(), name="portal_logout"),
    path("portal/", views.dashboard, name="portal_home"),
    path("portal/appointments/", views.records, {"kind": "appointments"}, name="portal_appointments"),
    path("portal/visits/", views.records, {"kind": "visits"}, name="portal_visits"),
    path("portal/medications/", views.records, {"kind": "medications"}, name="portal_medications"),
    path("portal/results/", views.results, name="portal_results"),
    path("portal/results/<int:result_id>/", views.results, name="portal_result"),
    path("portal/messages/", communication_views.messages, name="portal_messages"),
    path("portal/messages/new/", communication_views.new_message, name="portal_message_new"),
    path("portal/messages/<int:thread_id>/", communication_views.thread, name="portal_thread"),
    path("portal/requests/", communication_views.requests, name="portal_requests"),
    path("portal/requests/new/<str:kind>/", communication_views.new_request, name="portal_request_new"),
    path("portal/requests/<int:request_id>/", communication_views.request_detail, name="portal_request"),
    path("app/portal/messages/", communication_views.staff_messages, name="staff_portal_messages"),
    path("app/portal/messages/<int:thread_id>/", communication_views.staff_thread, name="staff_portal_thread"),
    path("app/portal/requests/", communication_views.staff_requests, name="staff_portal_requests"),
    path("app/portal/requests/<int:request_id>/", communication_views.staff_request_detail, name="staff_portal_request"),
    path("app/portal/releases/", views.releases, name="portal_releases"),
]
