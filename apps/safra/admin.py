from django.contrib import admin
from .models import Safra


@admin.register(Safra)
class SafraAdmin(admin.ModelAdmin):
    list_display = ["produtor", "cultura", "ano_safra", "producao_estimada_sacas", "ativa"]
    list_filter = ["cultura", "ativa"]
