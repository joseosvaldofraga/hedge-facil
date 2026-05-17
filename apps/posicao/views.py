import json
from decimal import Decimal
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from apps.safra.models import Safra
from .services import calcular_posicao, calcular_risco, get_cotacao_atual, get_cotacao_com_variacao, get_historico_cotacao


@login_required
def painel(request):
    safras_ativas = Safra.objects.filter(produtor=request.user, ativa=True)
    safras_inativas = Safra.objects.filter(produtor=request.user, ativa=False)
    mercado = get_cotacao_com_variacao()
    historico = get_historico_cotacao()
    cotacao = mercado["cotacao"]

    items = []
    for safra in safras_ativas:
        posicao = calcular_posicao(safra)
        risco = calcular_risco(posicao, safra, cotacao)
        base = None
        if safra.preco_referencia_local:
            base = (safra.preco_referencia_local - cotacao).quantize(Decimal("0.01"))
        insumos_cobertos = None
        if safra.total_insumos_brl:
            insumos_cobertos = posicao.receita_travada >= safra.total_insumos_brl
        items.append({
            "safra": safra,
            "posicao": posicao,
            "risco": risco,
            "base": base,
            "insumos_cobertos": insumos_cobertos,
        })

    receita_total = sum((i["posicao"].receita_travada for i in items), Decimal("0"))
    exposicao_total = sum(
        (i["posicao"].sacas_a_vender * cotacao for i in items), Decimal("0")
    ).quantize(Decimal("0.01"))
    custo_total = sum((i["posicao"].custo_total for i in items), Decimal("0"))

    return render(request, "posicao/painel.html", {
        "mercado": mercado,
        "cotacao": cotacao,
        "historico_json": json.dumps(historico),
        "items": items,
        "safras_inativas": safras_inativas,
        "receita_total": receita_total,
        "exposicao_total": exposicao_total,
        "custo_total": custo_total,
        "sem_safras": not items and not safras_inativas.exists(),
    })


@login_required
def pdf(request):
    safra = Safra.objects.filter(produtor=request.user, ativa=True).first()
    if not safra:
        return redirect("safra:nova")
    posicao = calcular_posicao(safra)
    cotacao = get_cotacao_atual()
    html = render_to_string("posicao/posicao_pdf.html", {
        "posicao": posicao,
        "safra": safra,
        "cotacao": cotacao,
    })
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="posicao_{safra.id}.pdf"'
    from xhtml2pdf import pisa
    status = pisa.CreatePDF(html, dest=response)
    if status.err:
        return HttpResponse("Erro ao gerar PDF", status=500)
    return response
