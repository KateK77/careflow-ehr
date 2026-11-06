from django.urls import path

from careflow.core import views


urlpatterns = [
    path("", views.home, name="home"),
    path("health/", views.health, name="health"),
]
