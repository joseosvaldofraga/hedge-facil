from django.urls import path
from . import views

app_name = "safra"

urlpatterns = [
    path("nova/", views.nova, name="nova"),
]
