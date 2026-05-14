from decimal import Decimal
from dataclasses import dataclass
from math import log, sqrt, exp, erf


@dataclass
class CenarioPreco:
    nome: str
    variacao_percentual: Decimal
    preco_projetado: Decimal
    receita_no_saldo: Decimal
    impacto_vs_atual: Decimal


_NOMES_PADRAO = {
    Decimal("-50"): "Queda extrema 50%",
    Decimal("-35"): "Queda severa 35%",
    Decimal("-20"): "Queda 20%",
    Decimal("0"):   "Preço estável",
    Decimal("15"):  "Alta 15%",
    Decimal("30"):  "Alta forte 30%",
}


def _norm_cdf(x: float) -> float:
    return (1.0 + erf(x / sqrt(2.0))) / 2.0


def black_scholes_put(S: Decimal, K: Decimal, T_anos: Decimal, r: float = 0.105, sigma: float = 0.35) -> Decimal:
    S_f, K_f, T_f = float(S), float(K), float(T_anos)
    if T_f <= 0 or sigma <= 0 or S_f <= 0 or K_f <= 0:
        return max(K - S, Decimal("0")).quantize(Decimal("0.01"))
    d1 = (log(S_f / K_f) + (r + 0.5 * sigma ** 2) * T_f) / (sigma * sqrt(T_f))
    d2 = d1 - sigma * sqrt(T_f)
    put = K_f * exp(-r * T_f) * _norm_cdf(-d2) - S_f * _norm_cdf(-d1)
    return Decimal(str(max(put, 0.0))).quantize(Decimal("0.01"))


def black_scholes_call(S: Decimal, K: Decimal, T_anos: Decimal, r: float = 0.105, sigma: float = 0.35) -> Decimal:
    S_f, K_f, T_f = float(S), float(K), float(T_anos)
    if T_f <= 0 or sigma <= 0 or S_f <= 0 or K_f <= 0:
        return max(S - K, Decimal("0")).quantize(Decimal("0.01"))
    d1 = (log(S_f / K_f) + (r + 0.5 * sigma ** 2) * T_f) / (sigma * sqrt(T_f))
    d2 = d1 - sigma * sqrt(T_f)
    call = S_f * _norm_cdf(d1) - K_f * exp(-r * T_f) * _norm_cdf(d2)
    return Decimal(str(max(call, 0.0))).quantize(Decimal("0.01"))


def calcular_volatilidade_historica(historico: list) -> float:
    precos = [h["preco"] for h in historico if h.get("preco", 0) > 0]
    if len(precos) < 5:
        return 0.35
    retornos = [log(precos[i] / precos[i - 1]) for i in range(1, len(precos))]
    media = sum(retornos) / len(retornos)
    variancia = sum((r - media) ** 2 for r in retornos) / (len(retornos) - 1)
    return sqrt(variancia) * sqrt(252)


def simular_estrategias(
    cotacao: Decimal,
    custo: Decimal,
    strike_put: Decimal,
    meses: int,
    historico: list,
) -> dict:
    T_anos = Decimal(str(meses)) / Decimal("12")
    sigma = calcular_volatilidade_historica(historico)
    strike_call = (strike_put * Decimal("1.20")).quantize(Decimal("0.01"))

    premio_put = black_scholes_put(cotacao, strike_put, T_anos, sigma=sigma)
    premio_call = black_scholes_call(cotacao, strike_call, T_anos, sigma=sigma)

    n_pontos = 31
    step = cotacao * Decimal("0.8") / Decimal(str(n_pontos - 1))
    pontos = []
    for i in range(n_pontos):
        P = (cotacao * Decimal("0.60") + step * Decimal(str(i))).quantize(Decimal("0.01"))
        sem_protecao = float((P - custo).quantize(Decimal("0.01")))
        futuro = float((cotacao - custo).quantize(Decimal("0.01")))  # contrato travado ao preço atual
        put = float((max(P, strike_put) - custo - premio_put).quantize(Decimal("0.01")))
        collar_preco = max(strike_put, min(P, strike_call))
        collar = float((collar_preco + premio_call - premio_put - custo).quantize(Decimal("0.01")))
        pontos.append({
            "preco": float(P),
            "sem_protecao": sem_protecao,
            "futuro": futuro,
            "put": put,
            "collar": collar,
        })

    return {
        "pontos": pontos,
        "premio_put": premio_put,
        "premio_call": premio_call,
        "sigma": round(sigma * 100, 1),
        "strike_put": strike_put,
        "strike_call": strike_call,
    }


def simular_cenarios(
    preco_atual: Decimal,
    sacas_a_vender: Decimal = Decimal("1"),
    variacoes: list[Decimal] = None,
) -> list[CenarioPreco]:
    if variacoes is None:
        variacoes = [Decimal("-50"), Decimal("-35"), Decimal("-20"), Decimal("0"), Decimal("15"), Decimal("30")]

    receita_estavel = sacas_a_vender * preco_atual
    cenarios = []

    for var in variacoes:
        preco = preco_atual * (Decimal("1") + var / Decimal("100"))
        receita = sacas_a_vender * preco
        impacto = receita - receita_estavel

        cenarios.append(CenarioPreco(
            nome=_NOMES_PADRAO.get(var, f"Variação {var}%"),
            variacao_percentual=var,
            preco_projetado=preco.quantize(Decimal("0.01")),
            receita_no_saldo=receita.quantize(Decimal("0.01")),
            impacto_vs_atual=impacto.quantize(Decimal("0.01")),
        ))

    return cenarios
