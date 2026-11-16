from django.urls import path
from . import views

urlpatterns = [
    path("accounts/register/<str:kind>/", views.signup, name="account_signup"),
    path("accounts/complete/<str:kind>/", views.complete, name="account_complete"),
    path("app/accounts/applications/", views.applications, name="account_applications"),
    path("app/accounts/applications/<int:pk>/", views.application, name="account_application"),
]
