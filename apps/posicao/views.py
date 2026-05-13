from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from apps.safra.models import Safra
from .services import calcular_posicao, get_cotacao_atual


@login_required
def painel(request):
    safra = Safra.objects.filter(produtor=request.user, ativa=True).first()
    if not safra:
        return redirect("safra:nova")
    posicao = calcular_posicao(safra)
    cotacao = get_cotacao_atual()
    return render(request, "posicao/painel.html", {
        "posicao": posicao,
        "safra": safra,
        "cotacao": cotacao,
    })
