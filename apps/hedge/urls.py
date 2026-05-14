from django.urls import path
from . import views

app_name = "hedge"

urlpatterns = [
    path("", views.hedge_redirect, name="redirect"),
    path("<int:safra_id>/cenarios/", views.cenarios, name="cenarios"),
    path("<int:safra_id>/proteger/", views.proteger, name="proteger"),
    path("<int:safra_id>/estrategias/", views.estrategias, name="estrategias"),
]
