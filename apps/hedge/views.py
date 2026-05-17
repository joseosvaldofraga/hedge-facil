import json
from datetime import datetime, date as date_type
from decimal import Decimal, InvalidOperation
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from apps.safra.models import Safra
from apps.posicao.services import calcular_posicao, get_cotacao_atual, get_historico_cotacao, get_chain_opcoes
from .services import (
    calcular_volatilidade_historica, simular_cenarios, simular_estrategias,
    _selecionar_cards, black_scholes_delta_put, black_scholes_theta_put_dia,
)


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


_MESES_PT = {
    1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr',
    5: 'Mai', 6: 'Jun', 7: 'Jul', 8: 'Ago',
    9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez',
}


@login_required
def opcoes(request, safra_id):
    safra = get_object_or_404(Safra, id=safra_id, produtor=request.user)
    posicao = calcular_posicao(safra)

    chain = get_chain_opcoes(safra.cultura, request.GET.get('venc', ''))
    cultura_disponivel = bool(chain['vencimentos'])

    if not cultura_disponivel:
        return render(request, 'hedge/opcoes.html', {
            'safra': safra,
            'posicao': posicao,
            'cultura_disponivel': False,
        })

    cards = _selecionar_cards(chain['puts'], safra.custo_por_saca, chain['cotacao_brl'])

    # Calcular cenário queda 25% para cada card
    cotacao = chain['cotacao_brl']
    custo = safra.custo_por_saca
    for card in cards:
        card['custo_total_safra'] = float(posicao.sacas_a_vender * card['premio_brl'])
        preco_queda = cotacao * Decimal('0.75')
        lucro_q = posicao.sacas_a_vender * (max(preco_queda, card['strike_brl']) - custo - card['premio_brl'])
        if lucro_q >= Decimal('-50'):
            card['cenario_queda'] = 'você fica praticamente no zero'
        elif lucro_q >= 0:
            card['cenario_queda'] = f'você ainda lucra R$ {int(lucro_q):,}'.replace(',', '.')
        else:
            card['cenario_queda'] = f'você perde R$ {int(abs(lucro_q)):,}'.replace(',', '.')

    # Adicionar iv_label para a seção avançada
    for put in chain['puts']:
        iv = put['iv']
        if iv < 25:
            put['iv_label'] = 'mercado calmo'
        elif iv < 40:
            put['iv_label'] = 'mercado moderado'
        else:
            put['iv_label'] = 'mercado agitado'

    # Greeks do card "Proteção do Custo" (cards[1]) para a seção avançada
    card_destaque = cards[1] if len(cards) > 1 else (cards[0] if cards else None)
    if card_destaque and chain['vencimento']:
        try:
            venc_date = datetime.strptime(chain['vencimento'], '%Y-%m-%d').date()
            T_anos = Decimal(str(max((venc_date - date_type.today()).days, 1) / 365))
            sigma = card_destaque['iv'] / 100
            card_destaque['delta'] = black_scholes_delta_put(
                cotacao, card_destaque['strike_brl'], T_anos, sigma=sigma
            )
            card_destaque['delta_abs'] = round(abs(card_destaque['delta']), 2)
            card_destaque['theta_dia'] = abs(black_scholes_theta_put_dia(
                cotacao, card_destaque['strike_brl'], T_anos, sigma=sigma
            ))
        except (ValueError, TypeError):
            pass

    # Formatar vencimentos para chips legíveis
    vencimentos_fmt = []
    for v in chain['vencimentos'][:5]:
        try:
            dt = datetime.strptime(v, '%Y-%m-%d')
            vencimentos_fmt.append({'value': v, 'label': f"{_MESES_PT[dt.month]} {dt.year}"})
        except ValueError:
            vencimentos_fmt.append({'value': v, 'label': v})

    # JSON para simulador JS (Decimal → float)
    cards_json = json.dumps([
        {
            'nome':       c['nome'],
            'strike_brl': float(c['strike_brl']),
            'premio_brl': float(c['premio_brl']),
        }
        for c in cards
    ])

    has_greeks = card_destaque is not None and 'delta' in card_destaque

    return render(request, 'hedge/opcoes.html', {
        'safra':              safra,
        'posicao':            posicao,
        'cultura_disponivel': True,
        'cards':              cards,
        'cards_json':         cards_json,
        'puts':               chain['puts'],
        'vencimentos_fmt':    vencimentos_fmt,
        'vencimento':         chain['vencimento'],
        'cotacao_brl':        cotacao,
        'card_destaque':      card_destaque,
        'has_greeks':         has_greeks,
    })
