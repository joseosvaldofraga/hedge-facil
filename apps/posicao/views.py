import json
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from apps.safra.models import Safra
from .services import calcular_posicao, calcular_risco, get_cotacao_atual, get_cotacao_com_variacao, get_historico_cotacao


@login_required
def painel(request):
    safra = Safra.objects.filter(produtor=request.user, ativa=True).first()
    mercado = get_cotacao_com_variacao()
    historico = get_historico_cotacao()
    cotacao = mercado["cotacao"]
    ctx = {
        "mercado": mercado,
        "cotacao": cotacao,
        "historico_json": json.dumps(historico),
        "safra": safra,
    }
    if safra:
        posicao = calcular_posicao(safra)
        risco = calcular_risco(posicao, safra, cotacao)
        ctx["posicao"] = posicao
        ctx["risco"] = risco
    return render(request, "posicao/painel.html", ctx)


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
