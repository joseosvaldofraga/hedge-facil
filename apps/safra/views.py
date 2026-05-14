from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db import transaction
from .forms import SafraForm
from .models import Safra


@login_required
def lista(request):
    safras = request.user.safras.all()
    return render(request, "safra/lista.html", {"safras": safras})


@login_required
def nova(request):
    if request.method == "POST":
        form = SafraForm(request.POST)
        if form.is_valid():
            safra = form.save(commit=False)
            safra.produtor = request.user
            safra.save()
            return redirect("posicao:painel")
    else:
        form = SafraForm()
    primeiro_acesso = request.user.safras.count() == 0
    return render(request, "safra/nova.html", {
        "form": form,
        "primeiro_acesso": primeiro_acesso,
    })


@login_required
@require_POST
def ativar(request, safra_id):
    safra = get_object_or_404(Safra, id=safra_id, produtor=request.user)
    with transaction.atomic():
        request.user.safras.update(ativa=False)
        safra.ativa = True
        safra.save()
    return redirect("posicao:painel")
