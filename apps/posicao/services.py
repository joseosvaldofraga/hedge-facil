from decimal import Decimal
from dataclasses import dataclass
from datetime import datetime, timedelta
from django.conf import settings
from django.core.cache import cache
from apps.safra.models import Safra


@dataclass
class PosicaoSafra:
    sacas_totais: Decimal
    sacas_vendidas: Decimal
    sacas_a_vender: Decimal
    percentual_vendido: Decimal
    preco_medio_ponderado: Decimal
    receita_travada: Decimal
    custo_total: Decimal
    lucro_travado_parcial: Decimal


@dataclass
class RiscoSafra:
    preco_ruina: Decimal
    margem_seguranca: Decimal
    pct_custo_coberto: Decimal
    em_zona_critica: bool
    sacas_travadas: Decimal
    sacas_com_piso: Decimal
    pct_convexo: Decimal
    convexidade_label: str
    exposicao_no_saldo: Decimal


def calcular_posicao(safra: Safra) -> PosicaoSafra:
    vendas = safra.vendas.all()
    sacas_vendidas = sum((v.sacas for v in vendas), Decimal("0"))
    receita_travada = sum((v.receita for v in vendas), Decimal("0"))

    if sacas_vendidas > 0:
        preco_medio = receita_travada / sacas_vendidas
    else:
        preco_medio = Decimal("0")

    sacas_a_vender = safra.producao_estimada_sacas - sacas_vendidas
    percentual = (
        sacas_vendidas / safra.producao_estimada_sacas * 100
        if safra.producao_estimada_sacas > 0
        else Decimal("0")
    )
    custo_proporcional = sacas_vendidas * safra.custo_por_saca
    lucro_parcial = receita_travada - custo_proporcional

    return PosicaoSafra(
        sacas_totais=safra.producao_estimada_sacas,
        sacas_vendidas=sacas_vendidas,
        sacas_a_vender=sacas_a_vender,
        percentual_vendido=percentual.quantize(Decimal("0.01")),
        preco_medio_ponderado=preco_medio.quantize(Decimal("0.01")),
        receita_travada=receita_travada.quantize(Decimal("0.01")),
        custo_total=safra.custo_total.quantize(Decimal("0.01")),
        lucro_travado_parcial=lucro_parcial.quantize(Decimal("0.01")),
    )


def calcular_risco(posicao: PosicaoSafra, safra: Safra, cotacao: Decimal, vendas=None) -> RiscoSafra:
    if vendas is None:
        vendas = list(safra.vendas.all())
    sacas_com_piso = sum(
        (v.sacas for v in vendas if v.tipo == "opcao_b3"), Decimal("0")
    )
    sacas_travadas = posicao.sacas_vendidas - sacas_com_piso

    if posicao.sacas_vendidas > Decimal("0"):
        pct_convexo = sacas_com_piso / posicao.sacas_vendidas * 100
    else:
        pct_convexo = Decimal("0")

    if posicao.sacas_vendidas == Decimal("0"):
        label = "Sem posição"
    elif sacas_com_piso == Decimal("0"):
        label = "Côncava"
    elif sacas_travadas == Decimal("0"):
        label = "Convexa"
    else:
        label = "Mista"

    preco_ruina = safra.custo_por_saca
    margem = cotacao - preco_ruina
    pct_coberto = (
        posicao.receita_travada / posicao.custo_total * 100
        if posicao.custo_total > Decimal("0")
        else Decimal("0")
    )
    em_zona_critica = cotacao < preco_ruina * Decimal("1.10")
    exposicao = posicao.sacas_a_vender * (cotacao - preco_ruina)

    return RiscoSafra(
        preco_ruina=preco_ruina.quantize(Decimal("0.01")),
        margem_seguranca=margem.quantize(Decimal("0.01")),
        pct_custo_coberto=pct_coberto.quantize(Decimal("0.01")),
        em_zona_critica=em_zona_critica,
        sacas_travadas=sacas_travadas.quantize(Decimal("0.01")),
        sacas_com_piso=sacas_com_piso.quantize(Decimal("0.01")),
        pct_convexo=pct_convexo.quantize(Decimal("0.01")),
        convexidade_label=label,
        exposicao_no_saldo=exposicao.quantize(Decimal("0.01")),
    )


_SACA_POR_BUSHEL = Decimal("60") / Decimal("27.2155")  # ≈ 2.2046


def _buscar_cotacao_yfinance() -> tuple[Decimal, Decimal]:
    """Retorna (cotacao_brl_saca, variacao_pct). Lança exceção se falhar."""
    import yfinance as yf
    tickers = yf.download(["ZS=F", "USDBRL=X"], period="5d", progress=False, auto_adjust=True)
    close = tickers["Close"]
    zs = close["ZS=F"].dropna()
    brl = close["USDBRL=X"].dropna()
    preco_cents = Decimal(str(float(zs.iloc[-1])))
    brl_rate = Decimal(str(float(brl.iloc[-1])))
    cotacao = (preco_cents / 100) * _SACA_POR_BUSHEL * brl_rate
    variacao = Decimal("0")
    if len(zs) >= 2:
        ontem = Decimal(str(float(zs.iloc[-2])))
        variacao = (preco_cents - ontem) / ontem * 100
    return cotacao.quantize(Decimal("0.01")), variacao.quantize(Decimal("0.01"))


def get_cotacao_com_variacao() -> dict:
    """Retorna {cotacao, variacao_pct, variacao_abs, fonte}."""
    cached = cache.get("cotacao_soja_completa")
    if cached is not None:
        return cached
    try:
        cotacao, variacao_pct = _buscar_cotacao_yfinance()
        variacao_abs = (cotacao * variacao_pct / 100).quantize(Decimal("0.01"))
        resultado = {
            "cotacao": cotacao,
            "variacao_pct": variacao_pct,
            "variacao_abs": variacao_abs,
            "fonte": "CME/B3",
        }
        cache.set("cotacao_soja_completa", resultado, 3600)
        return resultado
    except Exception:
        cotacao = Decimal(str(getattr(settings, "COTACAO_SOJA_PADRAO", "130.00")))
        return {
            "cotacao": cotacao,
            "variacao_pct": Decimal("0"),
            "variacao_abs": Decimal("0"),
            "fonte": "estimado",
        }


def get_historico_cotacao(dias: int = 30) -> list:
    """Retorna lista de {'data': 'DD/MM', 'preco': float} para Chart.js."""
    cached = cache.get("historico_cotacao_30d")
    if cached is not None:
        return cached
    try:
        import yfinance as yf
        end = datetime.today()
        start = end - timedelta(days=dias + 15)
        tickers = yf.download(["ZS=F", "USDBRL=X"], start=start, end=end, progress=False, auto_adjust=True)
        close = tickers["Close"]
        zs = close["ZS=F"].dropna()
        brl = close["USDBRL=X"].dropna()
        merged = zs.to_frame("zs").join(brl.to_frame("brl"), how="inner").tail(dias)
        resultado = []
        for idx, row in merged.iterrows():
            preco = (Decimal(str(float(row["zs"]))) / 100) * _SACA_POR_BUSHEL * Decimal(str(float(row["brl"])))
            resultado.append({"data": idx.strftime("%d/%m"), "preco": float(preco.quantize(Decimal("0.01")))})
        cache.set("historico_cotacao_30d", resultado, 3600)
        return resultado
    except Exception:
        return []


def get_cotacao_atual() -> Decimal:
    cached = cache.get("cotacao_soja_atual")
    if cached is not None:
        return Decimal(str(cached))
    try:
        cotacao, _ = _buscar_cotacao_yfinance()
        cache.set("cotacao_soja_atual", str(cotacao), 3600)
        return cotacao
    except Exception:
        return Decimal(str(getattr(settings, "COTACAO_SOJA_PADRAO", "130.00")))
