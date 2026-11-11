from django.urls import include, path

from careflow.core import views
from careflow.core.auth_views import DemoLoginView, DemoLogoutView


urlpatterns = [
    path("login/", DemoLoginView.as_view(), name="login"),
    path("logout/", DemoLogoutView.as_view(), name="logout"),
    path("app/", include("careflow.patients.urls")),
    path("app/", include("careflow.scheduling.urls")),
    path("app/", include("careflow.clinical.urls")),
    path("app/", include("careflow.history.urls")),
    path("app/", include("careflow.nursing.urls")),
    path("app/", include("careflow.labs.urls")),
    path("app/", include("careflow.medications.urls")),
    path("app/", include("careflow.mar.urls")),
    path("", include("careflow.portal.urls")),
    path("", include("careflow.billing.urls")),
    path("app/", include("careflow.imaging.urls")),
    path("app/", include("careflow.hospital.urls")),
    path("", views.home, name="home"),
    path("health/", views.health, name="health"),
]
