from django.urls import path
from . import views

app_name = "hedge"

urlpatterns = [
    path("<int:safra_id>/cenarios/", views.cenarios, name="cenarios"),
    path("<int:safra_id>/proteger/", views.proteger, name="proteger"),
]
