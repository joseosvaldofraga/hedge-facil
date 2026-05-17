from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from apps.contas.models import Produtor
from apps.safra.models import Safra
from unittest.mock import patch, MagicMock
import pandas as pd
from django.core.cache import cache


class HedgeViewsTestCase(TestCase):
    def setUp(self):
        self.produtor = Produtor.objects.create_user(
            username="ze", email="ze@test.com", password="senha123"
        )
        self.safra = Safra.objects.create(
            produtor=self.produtor,
            cultura="soja",
            ano_safra="2025/26",
            producao_estimada_sacas=Decimal("1000"),
            custo_por_saca=Decimal("80"),
        )
        self.client.force_login(self.produtor)

    def test_cenarios_retorna_200(self):
        response = self.client.get(reverse("hedge:cenarios", args=[self.safra.id]))
        self.assertEqual(response.status_code, 200)

    def test_cenarios_requer_login(self):
        self.client.logout()
        response = self.client.get(reverse("hedge:cenarios", args=[self.safra.id]))
        self.assertEqual(response.status_code, 302)

    def test_cenarios_contexto_tem_6_cenarios(self):
        response = self.client.get(reverse("hedge:cenarios", args=[self.safra.id]))
        self.assertEqual(len(response.context["cenarios"]), 6)

    def test_simular_cenarios_retorna_6_por_padrao(self):
        from apps.hedge.services import simular_cenarios
        cenarios = simular_cenarios(Decimal("130"))
        self.assertEqual(len(cenarios), 6)

    def test_cenarios_incluem_queda_50_e_alta_30(self):
        from apps.hedge.services import simular_cenarios
        cenarios = simular_cenarios(Decimal("130"))
        variacoes = [c.variacao_percentual for c in cenarios]
        self.assertIn(Decimal("-50"), variacoes)
        self.assertIn(Decimal("30"), variacoes)

    def test_cenarios_contexto_tem_safra(self):
        response = self.client.get(reverse("hedge:cenarios", args=[self.safra.id]))
        self.assertEqual(response.context["safra"], self.safra)

    def test_cenarios_404_para_safra_de_outro_produtor(self):
        outro = Produtor.objects.create_user(username="outro", email="outro@test.com")
        safra_outro = Safra.objects.create(
            produtor=outro, cultura="milho", ano_safra="2025/26",
            producao_estimada_sacas=Decimal("500"), custo_por_saca=Decimal("60"),
        )
        response = self.client.get(reverse("hedge:cenarios", args=[safra_outro.id]))
        self.assertEqual(response.status_code, 404)

    def test_proteger_retorna_200(self):
        response = self.client.get(reverse("hedge:proteger", args=[self.safra.id]))
        self.assertEqual(response.status_code, 200)

    def test_proteger_requer_login(self):
        self.client.logout()
        response = self.client.get(reverse("hedge:proteger", args=[self.safra.id]))
        self.assertEqual(response.status_code, 302)

    def test_cenarios_preco_invalido_retorna_200_com_fallback(self):
        url = reverse("hedge:cenarios", args=[self.safra.id]) + "?preco_atual=abc"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_cenarios_preco_vazio_retorna_200_com_fallback(self):
        url = reverse("hedge:cenarios", args=[self.safra.id]) + "?preco_atual="
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class HedgeRedirectTestCase(TestCase):
    def setUp(self):
        self.produtor = Produtor.objects.create_user(
            username="redir_test", email="redir_test@test.com", password="senha123"
        )
        self.client.force_login(self.produtor)

    def test_hedge_redirect_com_safra_redireciona_para_cenarios(self):
        safra = Safra.objects.create(
            produtor=self.produtor,
            cultura="soja",
            ano_safra="2025/26",
            producao_estimada_sacas=Decimal("1000"),
            custo_por_saca=Decimal("80"),
        )
        response = self.client.get(reverse("hedge:redirect"))
        self.assertRedirects(
            response,
            reverse("hedge:cenarios", args=[safra.id]),
            fetch_redirect_response=False,
        )

    def test_hedge_redirect_sem_safra_redireciona_para_nova_safra(self):
        response = self.client.get(reverse("hedge:redirect"))
        self.assertRedirects(
            response,
            reverse("safra:nova"),
            fetch_redirect_response=False,
        )

    def test_hedge_redirect_requer_login(self):
        self.client.logout()
        response = self.client.get(reverse("hedge:redirect"))
        self.assertEqual(response.status_code, 302)
        self.assertNotIn("cenarios", response["Location"])


from math import isfinite


class BlackScholesTestCase(TestCase):
    def test_put_retorna_decimal(self):
        from apps.hedge.services import black_scholes_put
        resultado = black_scholes_put(Decimal("130"), Decimal("130"), Decimal("0.5"))
        self.assertIsInstance(resultado, Decimal)

    def test_call_retorna_decimal(self):
        from apps.hedge.services import black_scholes_call
        resultado = black_scholes_call(Decimal("130"), Decimal("130"), Decimal("0.5"))
        self.assertIsInstance(resultado, Decimal)

    def test_put_otm_menor_que_put_itm(self):
        from apps.hedge.services import black_scholes_put
        put_itm = black_scholes_put(Decimal("130"), Decimal("140"), Decimal("0.5"))
        put_otm = black_scholes_put(Decimal("130"), Decimal("120"), Decimal("0.5"))
        self.assertGreater(put_itm, put_otm)

    def test_volatilidade_fallback_quando_poucos_dados(self):
        from apps.hedge.services import calcular_volatilidade_historica
        resultado = calcular_volatilidade_historica([{"preco": 130.0}, {"preco": 131.0}])
        self.assertEqual(resultado, 0.35)

    def test_volatilidade_retorna_float(self):
        from apps.hedge.services import calcular_volatilidade_historica
        dados = [{"preco": 130.0 + i * 0.5} for i in range(10)]
        resultado = calcular_volatilidade_historica(dados)
        self.assertIsInstance(resultado, float)
        self.assertTrue(isfinite(resultado))


class SimularEstrategiasTestCase(TestCase):
    def _historico(self):
        return [{"preco": 130.0 + i * 0.5} for i in range(30)]

    def test_retorna_31_pontos(self):
        from apps.hedge.services import simular_estrategias
        r = simular_estrategias(Decimal("130"), Decimal("80"), Decimal("130"), 6, self._historico())
        self.assertEqual(len(r["pontos"]), 31)

    def test_futuro_e_linha_constante(self):
        from apps.hedge.services import simular_estrategias
        r = simular_estrategias(Decimal("130"), Decimal("80"), Decimal("130"), 6, self._historico())
        lucros = [p["futuro"] for p in r["pontos"]]
        self.assertEqual(len(set(lucros)), 1)

    def test_sem_protecao_cresce_com_preco(self):
        from apps.hedge.services import simular_estrategias
        r = simular_estrategias(Decimal("130"), Decimal("80"), Decimal("130"), 6, self._historico())
        lucros = [p["sem_protecao"] for p in r["pontos"]]
        self.assertEqual(lucros, sorted(lucros))

    def test_put_limitada_pelo_piso(self):
        from apps.hedge.services import simular_estrategias
        r = simular_estrategias(Decimal("130"), Decimal("80"), Decimal("130"), 6, self._historico())
        premio = r["premio_put"]
        piso = float(Decimal("130") - Decimal("80") - premio)
        lucros = [p["put"] for p in r["pontos"]]
        self.assertAlmostEqual(min(lucros), piso, places=0)

    def test_collar_limitado_pelo_teto(self):
        from apps.hedge.services import simular_estrategias
        r = simular_estrategias(Decimal("130"), Decimal("80"), Decimal("130"), 6, self._historico())
        lucros = [p["collar"] for p in r["pontos"]]
        max_collar = max(lucros)
        for l in lucros[-5:]:
            self.assertAlmostEqual(l, max_collar, places=0)

    def test_resultado_tem_chaves_necessarias(self):
        from apps.hedge.services import simular_estrategias
        r = simular_estrategias(Decimal("130"), Decimal("80"), Decimal("130"), 6, self._historico())
        self.assertIn("pontos", r)
        self.assertIn("premio_put", r)
        self.assertIn("premio_call", r)
        self.assertIn("sigma", r)
        self.assertIn("strike_call", r)


class EstrategiasViewTestCase(TestCase):
    def setUp(self):
        self.produtor = Produtor.objects.create_user(
            username="estrat", email="estrat@test.com", password="senha123"
        )
        self.safra = Safra.objects.create(
            produtor=self.produtor,
            cultura="soja",
            ano_safra="2025/26",
            producao_estimada_sacas=Decimal("1000"),
            custo_por_saca=Decimal("80"),
        )
        self.client.force_login(self.produtor)

    def test_estrategias_retorna_200(self):
        response = self.client.get(reverse("hedge:estrategias", args=[self.safra.id]))
        self.assertEqual(response.status_code, 200)

    def test_estrategias_requer_login(self):
        self.client.logout()
        response = self.client.get(reverse("hedge:estrategias", args=[self.safra.id]))
        self.assertEqual(response.status_code, 302)

    def test_estrategias_404_para_safra_de_outro_produtor(self):
        outro = Produtor.objects.create_user(username="outro2", email="outro2@test.com")
        safra_outro = Safra.objects.create(
            produtor=outro, cultura="soja", ano_safra="2025/26",
            producao_estimada_sacas=Decimal("500"), custo_por_saca=Decimal("60"),
        )
        response = self.client.get(reverse("hedge:estrategias", args=[safra_outro.id]))
        self.assertEqual(response.status_code, 404)

    def test_estrategias_contexto_tem_pontos_json(self):
        response = self.client.get(reverse("hedge:estrategias", args=[self.safra.id]))
        self.assertIn("pontos_json", response.context)
        import json
        pontos = json.loads(response.context["pontos_json"])
        self.assertEqual(len(pontos), 31)


class GetChainOpcoesTestCase(TestCase):

    def setUp(self):
        cache.clear()

    def _puts_df(self):
        return pd.DataFrame({
            'strike':            [1200.0, 1300.0, 1400.0],
            'lastPrice':         [5.0,    10.0,   20.0],
            'bid':               [4.8,    9.8,    19.8],
            'volume':            [100.0,  200.0,  0.0],
            'openInterest':      [500.0,  1000.0, 0.0],
            'impliedVolatility': [0.28,   0.32,   0.35],
        })

    def _mock_ticker(self):
        ticker = MagicMock()
        ticker.options = ['2026-03-21', '2026-05-16']
        chain = MagicMock()
        chain.puts = self._puts_df()
        ticker.option_chain.return_value = chain
        return ticker

    def _brl_df(self):
        return pd.DataFrame(
            {'Close': [5.75, 5.80]},
            index=pd.to_datetime(['2026-03-19', '2026-03-20'])
        )

    @patch('apps.posicao.services.get_cotacao_com_variacao')
    @patch('yfinance.download')
    @patch('yfinance.Ticker')
    def test_get_chain_opcoes_retorna_estrutura_esperada(self, mock_ticker_cls, mock_download, mock_cotacao):
        mock_ticker_cls.return_value = self._mock_ticker()
        mock_download.return_value = self._brl_df()
        mock_cotacao.return_value = {
            'cotacao': Decimal('130.00'), 'variacao_pct': Decimal('0'),
            'variacao_abs': Decimal('0'), 'fonte': 'test',
        }
        from apps.posicao.services import get_chain_opcoes
        result = get_chain_opcoes('soja', '')
        self.assertIn('puts', result)
        self.assertIn('vencimentos', result)
        self.assertIn('cotacao_brl', result)
        self.assertIn('cambio', result)
        self.assertIn('vencimento', result)
        self.assertIsInstance(result['puts'], list)
        self.assertEqual(result['vencimentos'], ['2026-03-21', '2026-05-16'])

    @patch('apps.posicao.services.get_cotacao_com_variacao')
    @patch('yfinance.download')
    @patch('yfinance.Ticker')
    def test_get_chain_opcoes_converte_para_brl(self, mock_ticker_cls, mock_download, mock_cotacao):
        mock_ticker_cls.return_value = self._mock_ticker()
        mock_download.return_value = self._brl_df()
        mock_cotacao.return_value = {
            'cotacao': Decimal('130.00'), 'variacao_pct': Decimal('0'),
            'variacao_abs': Decimal('0'), 'fonte': 'test',
        }
        from apps.posicao.services import get_chain_opcoes, _SACA_POR_BUSHEL
        result = get_chain_opcoes('soja', '2026-03-21')
        # strike 1200 cents/bushel, cambio 5.80
        # strike_brl = (1200 * _SACA_POR_BUSHEL * 5.80 / 100).quantize('0.01')
        expected = (Decimal('1200') * _SACA_POR_BUSHEL * Decimal('5.80') / 100).quantize(Decimal('0.01'))
        self.assertEqual(result['puts'][0]['strike_brl'], expected)

    @patch('apps.posicao.services.get_cotacao_com_variacao')
    @patch('yfinance.download')
    @patch('yfinance.Ticker')
    def test_get_chain_opcoes_filtra_sem_liquidez(self, mock_ticker_cls, mock_download, mock_cotacao):
        mock_ticker_cls.return_value = self._mock_ticker()
        mock_download.return_value = self._brl_df()
        mock_cotacao.return_value = {
            'cotacao': Decimal('130.00'), 'variacao_pct': Decimal('0'),
            'variacao_abs': Decimal('0'), 'fonte': 'test',
        }
        from apps.posicao.services import get_chain_opcoes
        result = get_chain_opcoes('soja', '2026-03-21')
        # 3ª linha da _puts_df tem volume=0 E openInterest=0 → deve ser filtrada
        self.assertEqual(len(result['puts']), 2)
