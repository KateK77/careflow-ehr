from django.urls import path

from . import views, workspace_views

urlpatterns = [
    path("radiology/", workspace_views.worklist, name="imaging_workspace"),
    path("radiology/exams/<int:order_id>/", workspace_views.exam_detail, name="imaging_exam"),
    path("imaging/review/", workspace_views.review_worklist, name="imaging_review_worklist"),
    path("imaging/orders/<int:order_id>/report/", workspace_views.report_detail, name="imaging_report"),
    path("imaging/catalog/", views.catalog, name="imaging_catalog"),
    path("imaging/orders/<int:order_id>/", views.order_detail, name="imaging_order"),
    path("patients/<int:patient_id>/encounters/<int:encounter_id>/imaging/new/", views.order_new, name="imaging_order_new"),
    path("patients/<int:patient_id>/imaging/", views.patient_orders, name="imaging_patient"),
]
