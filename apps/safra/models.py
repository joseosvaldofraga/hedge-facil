from decimal import Decimal
from django.db import models
from django.conf import settings


class Cultura(models.TextChoices):
    SOJA = "soja", "Soja"
    MILHO = "milho", "Milho"
    CAFE = "cafe", "Café"
    CANA = "cana", "Cana-de-açúcar"
    TRIGO = "trigo", "Trigo"


class Safra(models.Model):
    produtor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="safras",
    )
    cultura = models.CharField(max_length=20, choices=Cultura.choices)
    ano_safra = models.CharField(max_length=10, help_text="Ex: 2025/26")
    producao_estimada_sacas = models.DecimalField(max_digits=12, decimal_places=2)
    custo_por_saca = models.DecimalField(max_digits=10, decimal_places=2)
    cidade = models.CharField(max_length=100, blank=True)
    estado = models.CharField(max_length=2, blank=True)
    ativa = models.BooleanField(default=True)
    total_insumos_brl = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True,
        help_text="Custo total de insumos da safra (R$)",
    )
    pct_insumos_dolar = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True, default=Decimal("0"),
        help_text="% do custo de insumos atrelado ao dólar (0–100)",
    )
    preco_referencia_local = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Preço local informado pelo produtor (cooperativa/trader), R$/sc",
    )
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("produtor", "cultura", "ano_safra")]
        ordering = ["-criada_em"]

    def __str__(self):
        return f"{self.get_cultura_display()} {self.ano_safra} — {self.produtor.username}"

    @property
    def custo_total(self) -> Decimal:
        return self.producao_estimada_sacas * self.custo_por_saca

    @property
    def insumos_por_saca(self) -> Decimal:
        if self.total_insumos_brl and self.producao_estimada_sacas > 0:
            return (self.total_insumos_brl / self.producao_estimada_sacas).quantize(Decimal("0.01"))
        return Decimal("0")
