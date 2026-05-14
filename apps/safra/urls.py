from django.urls import path
from . import views

app_name = "safra"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("nova/", views.nova, name="nova"),
    path("<int:safra_id>/ativar/", views.ativar, name="ativar"),
]
