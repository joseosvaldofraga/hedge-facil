from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Produtor


@admin.register(Produtor)
class ProdutorAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Dados do Produtor", {"fields": ("whatsapp", "cidade", "estado", "aceitou_termos_em")}),
    )
