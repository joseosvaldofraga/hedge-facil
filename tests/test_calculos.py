from decimal import Decimal
from django.test import TestCase
from apps.contas.models import Produtor
from apps.safra.models import Safra
from apps.vendas.models import Venda
from apps.posicao.services import calcular_posicao


class CalcularPosicaoTestCase(TestCase):
    def setUp(self):
        self.produtor = Produtor.objects.create_user(username="ze", email="ze@test.com")
        self.safra = Safra.objects.create(
            produtor=self.produtor,
            cultura="soja",
            ano_safra="2025/26",
            producao_estimada_sacas=Decimal("1000"),
            custo_por_saca=Decimal("80"),
        )

    def _cria_venda(self, sacas, preco):
        return Venda.objects.create(
            safra=self.safra,
            tipo="balcao",
            contraparte="Cargill",
            sacas=Decimal(str(sacas)),
            preco_por_saca=Decimal(str(preco)),
            data_negociacao="2025-03-01",
        )

    def test_sem_vendas_sacas_vendidas_zero(self):
        posicao = calcular_posicao(self.safra)
        self.assertEqual(posicao.sacas_vendidas, Decimal("0"))

    def test_sem_vendas_preco_medio_zero(self):
        posicao = calcular_posicao(self.safra)
        self.assertEqual(posicao.preco_medio_ponderado, Decimal("0"))

    def test_sem_vendas_percentual_zero(self):
        posicao = calcular_posicao(self.safra)
        self.assertEqual(posicao.percentual_vendido, Decimal("0.00"))

    def test_preco_medio_ponderado_uma_venda(self):
        self._cria_venda(300, "120")
        posicao = calcular_posicao(self.safra)
        self.assertEqual(posicao.preco_medio_ponderado, Decimal("120.00"))

    def test_preco_medio_ponderado_duas_vendas(self):
        self._cria_venda(300, "120")
        self._cria_venda(200, "140")
        # (300*120 + 200*140) / 500 = (36000+28000)/500 = 128.00
        posicao = calcular_posicao(self.safra)
        self.assertEqual(posicao.preco_medio_ponderado, Decimal("128.00"))

    def test_sacas_a_vender_correto(self):
        self._cria_venda(300, "120")
        posicao = calcular_posicao(self.safra)
        self.assertEqual(posicao.sacas_a_vender, Decimal("700"))

    def test_percentual_vendido_correto(self):
        self._cria_venda(250, "120")
        posicao = calcular_posicao(self.safra)
        self.assertEqual(posicao.percentual_vendido, Decimal("25.00"))

    def test_receita_travada_soma_todas_vendas(self):
        self._cria_venda(300, "120")
        self._cria_venda(200, "140")
        # 300*120 + 200*140 = 36000 + 28000 = 64000
        posicao = calcular_posicao(self.safra)
        self.assertEqual(posicao.receita_travada, Decimal("64000.00"))

    def test_lucro_parcial_correto(self):
        self._cria_venda(300, "120")
        # receita=36000, custo=300*80=24000, lucro=12000
        posicao = calcular_posicao(self.safra)
        self.assertEqual(posicao.lucro_travado_parcial, Decimal("12000.00"))

    def test_custo_total_da_safra_inteira(self):
        posicao = calcular_posicao(self.safra)
        # 1000 * 80 = 80000
        self.assertEqual(posicao.custo_total, Decimal("80000.00"))

    def test_sacas_totais_iguais_producao_estimada(self):
        posicao = calcular_posicao(self.safra)
        self.assertEqual(posicao.sacas_totais, Decimal("1000"))


import unittest


class SimularCenariosTestCase(unittest.TestCase):
    def test_retorna_3_cenarios_por_padrao(self):
        from apps.hedge.services import simular_cenarios
        cenarios = simular_cenarios(
            sacas_a_vender=Decimal("700"),
            preco_atual=Decimal("130"),
        )
        self.assertEqual(len(cenarios), 3)

    def test_cenario_estavel_variacao_zero_impacto_zero(self):
        from apps.hedge.services import simular_cenarios
        cenarios = simular_cenarios(
            sacas_a_vender=Decimal("700"),
            preco_atual=Decimal("130"),
        )
        estavel = next(c for c in cenarios if c.variacao_percentual == Decimal("0"))
        self.assertEqual(estavel.impacto_vs_atual, Decimal("0.00"))

    def test_cenario_queda_20_preco_projetado_correto(self):
        from apps.hedge.services import simular_cenarios
        cenarios = simular_cenarios(
            sacas_a_vender=Decimal("700"),
            preco_atual=Decimal("130"),
        )
        queda = next(c for c in cenarios if c.variacao_percentual == Decimal("-20"))
        self.assertEqual(queda.preco_projetado, Decimal("104.00"))

    def test_cenario_queda_20_receita_correta(self):
        from apps.hedge.services import simular_cenarios
        cenarios = simular_cenarios(
            sacas_a_vender=Decimal("700"),
            preco_atual=Decimal("130"),
        )
        queda = next(c for c in cenarios if c.variacao_percentual == Decimal("-20"))
        self.assertEqual(queda.receita_no_saldo, Decimal("72800.00"))

    def test_cenario_queda_impacto_negativo(self):
        from apps.hedge.services import simular_cenarios
        cenarios = simular_cenarios(
            sacas_a_vender=Decimal("700"),
            preco_atual=Decimal("130"),
        )
        queda = next(c for c in cenarios if c.variacao_percentual == Decimal("-20"))
        self.assertLess(queda.impacto_vs_atual, Decimal("0"))

    def test_cenario_alta_15_preco_projetado_correto(self):
        from apps.hedge.services import simular_cenarios
        cenarios = simular_cenarios(
            sacas_a_vender=Decimal("700"),
            preco_atual=Decimal("130"),
        )
        alta = next(c for c in cenarios if c.variacao_percentual == Decimal("15"))
        self.assertEqual(alta.preco_projetado, Decimal("149.50"))

    def test_cenario_alta_15_receita_correta(self):
        from apps.hedge.services import simular_cenarios
        cenarios = simular_cenarios(
            sacas_a_vender=Decimal("700"),
            preco_atual=Decimal("130"),
        )
        alta = next(c for c in cenarios if c.variacao_percentual == Decimal("15"))
        self.assertEqual(alta.receita_no_saldo, Decimal("104650.00"))

    def test_cenario_alta_impacto_positivo(self):
        from apps.hedge.services import simular_cenarios
        cenarios = simular_cenarios(
            sacas_a_vender=Decimal("700"),
            preco_atual=Decimal("130"),
        )
        alta = next(c for c in cenarios if c.variacao_percentual == Decimal("15"))
        self.assertGreater(alta.impacto_vs_atual, Decimal("0"))

    def test_todos_valores_sao_decimal(self):
        from apps.hedge.services import simular_cenarios
        cenarios = simular_cenarios(
            sacas_a_vender=Decimal("700"),
            preco_atual=Decimal("130"),
        )
        for c in cenarios:
            self.assertIsInstance(c.preco_projetado, Decimal)
            self.assertIsInstance(c.receita_no_saldo, Decimal)
            self.assertIsInstance(c.impacto_vs_atual, Decimal)

    def test_variacoes_customizadas(self):
        from apps.hedge.services import simular_cenarios
        cenarios = simular_cenarios(
            sacas_a_vender=Decimal("500"),
            preco_atual=Decimal("100"),
            variacoes=[Decimal("-10"), Decimal("10")],
        )
        self.assertEqual(len(cenarios), 2)
