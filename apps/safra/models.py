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
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("produtor", "cultura", "ano_safra")]
        ordering = ["-criada_em"]

    def __str__(self):
        return f"{self.get_cultura_display()} {self.ano_safra} — {self.produtor.username}"

    @property
    def custo_total(self) -> Decimal:
        return self.producao_estimada_sacas * self.custo_por_saca
