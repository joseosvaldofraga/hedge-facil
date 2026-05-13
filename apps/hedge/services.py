from decimal import Decimal
from dataclasses import dataclass


@dataclass
class CenarioPreco:
    nome: str
    variacao_percentual: Decimal
    preco_projetado: Decimal
    receita_no_saldo: Decimal
    impacto_vs_atual: Decimal


_NOMES_PADRAO = {
    Decimal("-20"): "Preço cai 20%",
    Decimal("0"): "Preço fica igual",
    Decimal("15"): "Preço sobe 15%",
}


def simular_cenarios(
    sacas_a_vender: Decimal,
    preco_atual: Decimal,
    variacoes: list[Decimal] = None,
) -> list[CenarioPreco]:
    if variacoes is None:
        variacoes = [Decimal("-20"), Decimal("0"), Decimal("15")]

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
