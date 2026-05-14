from decimal import Decimal
from dataclasses import dataclass
from django.conf import settings
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


def calcular_risco(posicao: PosicaoSafra, safra: Safra, cotacao: Decimal) -> RiscoSafra:
    vendas = safra.vendas.all()
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
        sacas_travadas=sacas_travadas,
        sacas_com_piso=sacas_com_piso,
        pct_convexo=pct_convexo.quantize(Decimal("0.01")),
        convexidade_label=label,
        exposicao_no_saldo=exposicao.quantize(Decimal("0.01")),
    )


def get_cotacao_atual() -> Decimal:
    return Decimal(str(getattr(settings, "COTACAO_SOJA_PADRAO", "130.00")))
