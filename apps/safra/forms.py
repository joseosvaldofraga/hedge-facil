from django import forms
from .models import Safra


class SafraForm(forms.ModelForm):
    class Meta:
        model = Safra
        fields = [
            "cultura", "ano_safra", "producao_estimada_sacas", "custo_por_saca",
            "cidade", "estado",
            "total_insumos_brl", "pct_insumos_dolar", "preco_referencia_local",
        ]
        widgets = {
            "producao_estimada_sacas": forms.NumberInput(attrs={"placeholder": "Ex: 3000"}),
            "custo_por_saca": forms.NumberInput(attrs={"placeholder": "Ex: 80.00", "step": "0.01"}),
            "ano_safra": forms.TextInput(attrs={"placeholder": "Ex: 2025/26"}),
            "total_insumos_brl": forms.NumberInput(attrs={"placeholder": "Ex: 120000.00", "step": "0.01"}),
            "pct_insumos_dolar": forms.NumberInput(attrs={"placeholder": "Ex: 60", "step": "1", "min": "0", "max": "100"}),
            "preco_referencia_local": forms.NumberInput(attrs={"placeholder": "Ex: 121.50", "step": "0.01"}),
        }
