from django import forms
from .models import Venda


class VendaForm(forms.ModelForm):
    class Meta:
        model = Venda
        fields = ["tipo", "contraparte", "sacas", "preco_por_saca", "data_negociacao", "observacao"]
        widgets = {
            "data_negociacao": forms.DateInput(attrs={"type": "date"}),
            "sacas": forms.NumberInput(attrs={"placeholder": "Ex: 500"}),
            "preco_por_saca": forms.NumberInput(attrs={"placeholder": "Ex: 125.00", "step": "0.01"}),
        }
