from django.shortcuts import render, redirect
from django.contrib import auth
from django.contrib.auth.forms import AuthenticationForm
from django.views.decorators.http import require_POST
from .forms import RegisterForm


def landing_view(request):
    if request.user.is_authenticated:
        return redirect("posicao:painel")
    return render(request, "landing.html")


def login_view(request):
    form = AuthenticationForm(data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        auth.login(request, form.get_user())
        return redirect("posicao:painel")
    return render(request, "contas/login.html", {"form": form})


def register_view(request):
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        produtor = form.save()
        auth.login(request, produtor)
        return redirect("safra:nova")
    return render(request, "contas/registro.html", {"form": form})


@require_POST
def logout_view(request):
    auth.logout(request)
    return redirect("contas:login")
