from django.urls import path

from .views import corridor, geocode, health, plans

urlpatterns = [
    path("corridor-forecasts", corridor, name="corridor"),
    path("health", health, name="health"),
    path("geocode", geocode, name="geocode"),
    path("plans", plans, name="plans"),
]
