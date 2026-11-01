from django.urls import path

from .views import geocode, health, plans

urlpatterns = [
    path("health", health, name="health"),
    path("geocode", geocode, name="geocode"),
    path("plans", plans, name="plans"),
]
