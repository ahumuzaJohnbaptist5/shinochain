from django.urls import path
from .views import BatchEventView

urlpatterns = [
    path("events", BatchEventView.as_view(), name="analytics-events"),
]
