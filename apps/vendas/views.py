from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
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
    return render(request, "vendas/_form.html", {"form": form, "safra": safra})
