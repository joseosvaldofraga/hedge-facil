from django import forms
from .models import Safra


class SafraForm(forms.ModelForm):
    class Meta:
        model = Safra
        fields = ["cultura", "ano_safra", "producao_estimada_sacas", "custo_por_saca", "cidade", "estado"]
        widgets = {
            "producao_estimada_sacas": forms.NumberInput(attrs={"placeholder": "Ex: 3000"}),
            "custo_por_saca": forms.NumberInput(attrs={"placeholder": "Ex: 80.00", "step": "0.01"}),
            "ano_safra": forms.TextInput(attrs={"placeholder": "Ex: 2025/26"}),
        }
