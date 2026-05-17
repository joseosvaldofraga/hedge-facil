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
            'variacao_abs': Decimal('0'), 'cambio': Decimal('5.80'), 'fonte': 'test',
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
            'variacao_abs': Decimal('0'), 'cambio': Decimal('5.80'), 'fonte': 'test',
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
            'variacao_abs': Decimal('0'), 'cambio': Decimal('5.80'), 'fonte': 'test',
        }
        from apps.posicao.services import get_chain_opcoes
        result = get_chain_opcoes('soja', '2026-03-21')
        # 3ª linha da _puts_df tem volume=0 E openInterest=0 → deve ser filtrada
        self.assertEqual(len(result['puts']), 2)


class SelecionarCardsTestCase(TestCase):

    def setUp(self):
        self.puts = [
            {'strike_brl': Decimal('103.50'), 'premio_brl': Decimal('1.80'), 'volume': 100, 'open_interest': 500,  'iv': 28.0},
            {'strike_brl': Decimal('115.00'), 'premio_brl': Decimal('3.40'), 'volume': 200, 'open_interest': 1000, 'iv': 32.0},
            {'strike_brl': Decimal('120.00'), 'premio_brl': Decimal('5.10'), 'volume': 150, 'open_interest': 800,  'iv': 35.0},
            {'strike_brl': Decimal('130.00'), 'premio_brl': Decimal('7.20'), 'volume': 80,  'open_interest': 400,  'iv': 38.0},
        ]
        self.custo = Decimal('115.00')
        self.cotacao = Decimal('130.00')

    def test_selecionar_cards_retorna_tres_cards(self):
        from apps.hedge.services import _selecionar_cards
        cards = _selecionar_cards(self.puts, self.custo, self.cotacao)
        self.assertEqual(len(cards), 3)

    def test_card_custo_mais_proximo_do_break_even(self):
        from apps.hedge.services import _selecionar_cards
        cards = _selecionar_cards(self.puts, self.custo, self.cotacao)
        card_custo = cards[1]  # índice 1 = "Proteção do Custo"
        self.assertEqual(card_custo['nome'], 'Proteção do Custo')
        self.assertTrue(card_custo['destaque'])
        self.assertEqual(card_custo['strike_brl'], Decimal('115.00'))

    def test_card_protecao_total_e_atm(self):
        from apps.hedge.services import _selecionar_cards
        cards = _selecionar_cards(self.puts, self.custo, self.cotacao)
        card_total = cards[2]  # índice 2 = "Proteção Total"
        self.assertEqual(card_total['nome'], 'Proteção Total')
        self.assertEqual(card_total['strike_brl'], Decimal('130.00'))

    def test_selecionar_cards_lista_vazia_retorna_vazia(self):
        from apps.hedge.services import _selecionar_cards
        self.assertEqual(_selecionar_cards([], Decimal('115'), Decimal('130')), [])


class BlackScholesDeltaThetaTestCase(TestCase):

    def test_delta_put_esta_entre_menos_um_e_zero(self):
        from apps.hedge.services import black_scholes_delta_put
        delta = black_scholes_delta_put(Decimal('130'), Decimal('130'), Decimal('0.5'))
        self.assertGreaterEqual(delta, -1.0)
        self.assertLessEqual(delta, 0.0)

    def test_delta_put_atm_proximo_de_menos_meio(self):
        from apps.hedge.services import black_scholes_delta_put
        delta = black_scholes_delta_put(Decimal('130'), Decimal('130'), Decimal('0.5'))
        self.assertAlmostEqual(delta, -0.5, delta=0.15)

    def test_theta_put_e_negativo(self):
        from apps.hedge.services import black_scholes_theta_put_dia
        theta = black_scholes_theta_put_dia(Decimal('130'), Decimal('130'), Decimal('0.5'))
        self.assertLess(theta, 0)


class OpcoesViewTestCase(TestCase):

    def setUp(self):
        cache.clear()
        self.produtor = Produtor.objects.create_user(
            username='ze2', email='ze2@test.com', password='senha123'
        )
        self.safra = Safra.objects.create(
            produtor=self.produtor,
            cultura='soja',
            ano_safra='2025/26',
            producao_estimada_sacas=Decimal('1000'),
            custo_por_saca=Decimal('115'),
        )
        self.client.force_login(self.produtor)
        self.chain_mock = {
            'puts': [
                {'strike_brl': Decimal('103.50'), 'premio_brl': Decimal('1.80'), 'volume': 100, 'open_interest': 500,  'iv': 28.0},
                {'strike_brl': Decimal('115.00'), 'premio_brl': Decimal('3.40'), 'volume': 200, 'open_interest': 1000, 'iv': 32.0},
                {'strike_brl': Decimal('130.00'), 'premio_brl': Decimal('7.20'), 'volume': 80,  'open_interest': 400,  'iv': 38.0},
            ],
            'vencimentos': ['2026-03-21', '2026-05-16'],
            'vencimento':  '2026-03-21',
            'cotacao_brl': Decimal('130.00'),
            'cambio':      Decimal('5.80'),
        }

    @patch('apps.hedge.views.get_chain_opcoes')
    def test_opcoes_retorna_200(self, mock_chain):
        mock_chain.return_value = self.chain_mock
        response = self.client.get(reverse('hedge:opcoes', args=[self.safra.id]))
        self.assertEqual(response.status_code, 200)

    def test_opcoes_requer_login(self):
        self.client.logout()
        response = self.client.get(reverse('hedge:opcoes', args=[self.safra.id]))
        self.assertEqual(response.status_code, 302)

    @patch('apps.hedge.views.get_chain_opcoes')
    def test_opcoes_cultura_sem_suporte_mostra_aviso(self, mock_chain):
        safra_cana = Safra.objects.create(
            produtor=self.produtor, cultura='cana',
            ano_safra='2025/26', producao_estimada_sacas=Decimal('500'),
            custo_por_saca=Decimal('60'),
        )
        mock_chain.return_value = {
            'puts': [], 'vencimentos': [], 'vencimento': '',
            'cotacao_brl': Decimal('0'), 'cambio': Decimal('1'),
        }
        response = self.client.get(reverse('hedge:opcoes', args=[safra_cana.id]))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['cultura_disponivel'])

    @patch('apps.hedge.views.get_chain_opcoes')
    def test_opcoes_vencimento_default_e_primeiro_disponivel(self, mock_chain):
        mock_chain.return_value = self.chain_mock
        response = self.client.get(reverse('hedge:opcoes', args=[self.safra.id]))
        self.assertEqual(response.context['vencimento'], '2026-03-21')

    @patch('apps.hedge.views.get_chain_opcoes')
    def test_opcoes_cards_tem_cenario_queda(self, mock_chain):
        mock_chain.return_value = self.chain_mock
        response = self.client.get(reverse('hedge:opcoes', args=[self.safra.id]))
        cards = response.context['cards']
        # "Proteção Total" (strike=130, prêmio=7.20) com 1000 sacas expostas
        # queda 25%: max(130*0.75=97.50, 130) - 115 - 7.20 = 130 - 122.20 = 7.80/saca
        # lucro_q = 1000 * 7.80 = 7800 >= 0 → "você ainda lucra"
        card_total = cards[2]
        self.assertIn('ainda lucra', card_total['cenario_queda'])
