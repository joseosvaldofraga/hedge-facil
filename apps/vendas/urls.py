from django.urls import path
from . import views

app_name = "vendas"

urlpatterns = [
    path("<int:safra_id>/", views.lista, name="lista"),
    path("nova/<int:safra_id>/", views.nova, name="nova"),
    path("<int:venda_id>/editar/", views.editar, name="editar"),
    path("<int:venda_id>/deletar/", views.deletar, name="deletar"),
]
