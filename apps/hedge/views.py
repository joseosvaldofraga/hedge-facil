from decimal import Decimal, InvalidOperation
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from apps.safra.models import Safra
from apps.posicao.services import calcular_posicao
from .services import simular_cenarios


@login_required
def cenarios(request, safra_id):
    safra = get_object_or_404(Safra, id=safra_id, produtor=request.user)
    posicao = calcular_posicao(safra)
    try:
        preco_atual = Decimal(request.GET.get("preco_atual", "130"))
    except InvalidOperation:
        preco_atual = Decimal("130")
    lista_cenarios = simular_cenarios(
        sacas_a_vender=posicao.sacas_a_vender,
        preco_atual=preco_atual,
    )
    return render(request, "hedge/cenarios.html", {
        "cenarios": lista_cenarios,
        "safra": safra,
        "posicao": posicao,
        "preco_atual": preco_atual,
    })


@login_required
def proteger(request, safra_id):
    safra = get_object_or_404(Safra, id=safra_id, produtor=request.user)
    return render(request, "hedge/proteger.html", {"safra": safra})
