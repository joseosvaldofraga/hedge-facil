from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("", include("apps.contas.urls")),
    path("painel/", include("apps.posicao.urls")),
    path("safra/", include("apps.safra.urls")),
    path("vendas/", include("apps.vendas.urls")),
    path("hedge/", include("apps.hedge.urls")),
    path("admin/", admin.site.urls),
]
