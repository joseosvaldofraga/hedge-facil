from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from apps.safra.models import Safra
from .models import Venda
from .forms import VendaForm


@login_required
def lista(request, safra_id):
    safra = get_object_or_404(Safra, id=safra_id, produtor=request.user)
    vendas = safra.vendas.all()
    return render(request, "vendas/lista.html", {"vendas": vendas, "safra": safra})


@login_required
def nova(request, safra_id):
    safra = get_object_or_404(Safra, id=safra_id, produtor=request.user)
    if request.method == "POST":
        form = VendaForm(request.POST)
        if form.is_valid():
            venda = form.save(commit=False)
            venda.safra = safra
            venda.save()
            if request.htmx:
                return render(request, "vendas/_lista.html", {"vendas": safra.vendas.all(), "safra": safra})
            return redirect("posicao:painel")
    else:
        form = VendaForm()
    return render(request, "vendas/_form.html", {
        "form": form,
        "safra": safra,
        "action_url": reverse("vendas:nova", args=[safra.id]),
        "form_title": "Nova Venda",
    })


@login_required
def editar(request, venda_id):
    venda = get_object_or_404(Venda, id=venda_id, safra__produtor=request.user)
    safra = venda.safra
    if request.method == "POST":
        form = VendaForm(request.POST, instance=venda)
        if form.is_valid():
            form.save()
            if request.htmx:
                return render(request, "vendas/_lista.html", {
                    "vendas": safra.vendas.all(), "safra": safra,
                })
            return redirect("vendas:lista", safra_id=safra.id)
    else:
        form = VendaForm(instance=venda)
    return render(request, "vendas/_form.html", {
        "form": form,
        "safra": safra,
        "action_url": reverse("vendas:editar", args=[venda.id]),
        "form_title": "Editar Venda",
    })
