import json
from decimal import Decimal, InvalidOperation
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from apps.safra.models import Safra
from apps.posicao.services import calcular_posicao, get_cotacao_atual, get_historico_cotacao
from .services import simular_cenarios, simular_estrategias


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


@login_required
def hedge_redirect(request):
    safra = Safra.objects.filter(produtor=request.user, ativa=True).first()
    if safra:
        return redirect("hedge:cenarios", safra_id=safra.id)
    return redirect("safra:nova")


@login_required
def estrategias(request, safra_id):
    safra = get_object_or_404(Safra, id=safra_id, produtor=request.user)
    cotacao_base = get_cotacao_atual()
    historico = get_historico_cotacao()

    try:
        cotacao = Decimal(request.GET.get("cotacao", str(cotacao_base)))
    except InvalidOperation:
        cotacao = cotacao_base
    try:
        meses = max(1, min(12, int(request.GET.get("meses", "6"))))
    except (ValueError, TypeError):
        meses = 6
    try:
        pct_strike = max(Decimal("80"), min(Decimal("105"), Decimal(request.GET.get("pct_strike", "100"))))
    except InvalidOperation:
        pct_strike = Decimal("100")

    strike_put = (cotacao * pct_strike / 100).quantize(Decimal("0.01"))
    resultado = simular_estrategias(cotacao, safra.custo_por_saca, strike_put, meses, historico)

    variacoes_tabela = [Decimal("-0.40"), Decimal("-0.25"), Decimal("-0.15"),
                        Decimal("0"), Decimal("0.15"), Decimal("0.30"), Decimal("0.40")]
    tabela_pontos = []
    for var in variacoes_tabela:
        p_preco = (cotacao * (1 + var)).quantize(Decimal("0.01"))
        custo = safra.custo_por_saca
        sp = resultado["strike_put"]
        sc = resultado["strike_call"]
        pp = resultado["premio_put"]
        pc = resultado["premio_call"]
        sem_prot = float((p_preco - custo).quantize(Decimal("0.01")))
        futuro_val = float((cotacao - custo).quantize(Decimal("0.01")))
        put_val = float((max(p_preco, sp) - custo - pp).quantize(Decimal("0.01")))
        collar_preco = max(sp, min(p_preco, sc))
        collar_val = float((collar_preco + pc - pp - custo).quantize(Decimal("0.01")))
        tabela_pontos.append({
            "preco": p_preco,
            "sem_protecao": sem_prot,
            "futuro": futuro_val,
            "put": put_val,
            "collar": collar_val,
            "is_atual": var == Decimal("0"),
        })

    premio_liquido = (resultado["premio_put"] - resultado["premio_call"]).quantize(Decimal("0.01"))

    return render(request, "hedge/estrategias.html", {
        "safra": safra,
        "cotacao": cotacao,
        "meses": meses,
        "pct_strike": pct_strike,
        "strike_put": resultado["strike_put"],
        "strike_call": resultado["strike_call"],
        "premio_put": resultado["premio_put"],
        "premio_call": resultado["premio_call"],
        "premio_liquido": premio_liquido,
        "sigma": resultado["sigma"],
        "tabela_pontos": tabela_pontos,
        "pontos_json": json.dumps(resultado["pontos"]),
    })
