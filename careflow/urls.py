from django.urls import include, path

from careflow.core import views
from careflow.core.auth_views import DemoLoginView, DemoLogoutView


urlpatterns = [
    path("login/", DemoLoginView.as_view(), name="login"),
    path("logout/", DemoLogoutView.as_view(), name="logout"),
    path("app/", include("careflow.patients.urls")),
    path("app/", include("careflow.scheduling.urls")),
    path("", views.home, name="home"),
    path("health/", views.health, name="health"),
]
