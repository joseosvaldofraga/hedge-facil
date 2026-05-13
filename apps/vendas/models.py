from decimal import Decimal
from django.db import models


class TipoVenda(models.TextChoices):
    TERMO = "termo", "Contrato a Termo"
    CPR = "cpr", "CPR (Cédula de Produto Rural)"
    BALCAO = "balcao", "Venda Balcão"
    FUTURO_B3 = "futuro_b3", "Futuro B3"
    OPCAO_B3 = "opcao_b3", "Opção B3"


class Venda(models.Model):
    safra = models.ForeignKey(
        "safra.Safra",
        on_delete=models.CASCADE,
        related_name="vendas",
    )
    tipo = models.CharField(max_length=20, choices=TipoVenda.choices)
    contraparte = models.CharField(max_length=120, help_text="Cargill, Coopercitrus, BB, etc.")
    sacas = models.DecimalField(max_digits=12, decimal_places=2)
    preco_por_saca = models.DecimalField(max_digits=10, decimal_places=2)
    data_negociacao = models.DateField()
    observacao = models.TextField(blank=True)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-data_negociacao"]

    def __str__(self):
        return f"{self.contraparte} — {self.sacas} sc @ R$ {self.preco_por_saca}"

    @property
    def receita(self) -> Decimal:
        return self.sacas * self.preco_por_saca
