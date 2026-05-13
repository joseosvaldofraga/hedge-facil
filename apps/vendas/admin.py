from django.contrib import admin
from .models import Venda


@admin.register(Venda)
class VendaAdmin(admin.ModelAdmin):
    list_display = ["contraparte", "safra", "tipo", "sacas", "preco_por_saca", "data_negociacao"]
    list_filter = ["tipo"]
    date_hierarchy = "data_negociacao"
