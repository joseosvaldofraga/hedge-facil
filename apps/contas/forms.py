from django import forms
from django.contrib.auth.password_validation import validate_password
from .models import Produtor


class RegisterForm(forms.Form):
    username = forms.CharField(max_length=150, label="Usuário")
    email = forms.EmailField(label="Email")
    password1 = forms.CharField(widget=forms.PasswordInput, label="Senha")
    password2 = forms.CharField(widget=forms.PasswordInput, label="Confirmar senha")

    def clean_username(self):
        username = self.cleaned_data["username"]
        if Produtor.objects.filter(username=username).exists():
            raise forms.ValidationError("Este nome de usuário já está em uso.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password1")
        p2 = cleaned_data.get("password2")
        if p1 and p2:
            if p1 != p2:
                raise forms.ValidationError("As senhas não coincidem.")
            validate_password(p1)
        return cleaned_data

    def save(self):
        return Produtor.objects.create_user(
            username=self.cleaned_data["username"],
            email=self.cleaned_data["email"],
            password=self.cleaned_data["password1"],
        )
