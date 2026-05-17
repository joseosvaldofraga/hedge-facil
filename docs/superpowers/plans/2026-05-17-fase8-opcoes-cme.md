# Fase 8: Módulo de Opções CME — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Mostrar opções reais CME (via yfinance) em linguagem de produtor rural: 3 cards de proteção ancorados no custo da safra, simulador de custo total em JS, e seção avançada com IV, open interest e greeks explicados em português simples.

**Architecture:** `get_chain_opcoes` em `apps/posicao/services.py` (dados de mercado, mesma responsabilidade de `get_cotacao_com_variacao`). `_selecionar_cards`, `black_scholes_delta_put` e `black_scholes_theta_put_dia` em `apps/hedge/services.py` (lógica de estratégia). View `opcoes` em `apps/hedge/views.py`. Sem novos models, sem novas dependências.

**Tech Stack:** Django 6, yfinance (já instalado), pandas (já instalado via yfinance), Tailwind CDN, JS vanilla, Black-Scholes já em `apps/hedge/services.py`.

---

## Mapa de arquivos

| Arquivo | Ação |
|---------|------|
| `apps/posicao/services.py` | Adicionar `TICKER_CME`, `get_chain_opcoes` |
| `apps/hedge/services.py` | Adicionar `_selecionar_cards`, `black_scholes_delta_put`, `black_scholes_theta_put_dia` |
| `apps/hedge/views.py` | Adicionar view `opcoes` |
| `apps/hedge/urls.py` | Adicionar rota `<id>/opcoes/` |
| `apps/hedge/tests.py` | Adicionar 10 testes |
| `templates/hedge/opcoes.html` | Criar |
| `templates/hedge/cenarios.html` | Adicionar botão "Ver Opções" |
| `templates/hedge/estrategias.html` | Adicionar botão "Ver Opções" |

---

## Task 1: `get_chain_opcoes` em `apps/posicao/services.py`

**Files:**
- Modify: `apps/posicao/services.py`
- Modify: `apps/hedge/tests.py`

---

- [ ] **Step 1: Escrever os 3 testes RED em `apps/hedge/tests.py`**

Adicionar ao final do arquivo, após os imports existentes:

```python
# Novos imports no topo do arquivo (adicionar se não existirem)
from unittest.mock import patch, MagicMock
import pandas as pd
from django.core.cache import cache


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
```

- [ ] **Step 2: Rodar os testes para confirmar que falham**

```bash
cd /media/fragatec/SSD/projetos/web/hedgefacil
python manage.py test apps.hedge.tests.GetChainOpcoesTestCase -v 2
```

Esperado: `ImportError` ou `AttributeError` — `get_chain_opcoes` não existe ainda.

- [ ] **Step 3: Implementar `get_chain_opcoes` em `apps/posicao/services.py`**

Adicionar ao final do arquivo (após `get_cotacao_atual`):

```python
TICKER_CME = {
    "soja":  "ZS=F",
    "milho": "ZC=F",
    "cafe":  "KC=F",
}

_RESULTADO_VAZIO = {
    'puts': [], 'vencimentos': [], 'vencimento': '',
    'cotacao_brl': Decimal('0'), 'cambio': Decimal('1'),
}


def get_chain_opcoes(cultura: str, vencimento: str = '') -> dict:
    """
    Retorna chain de puts para a cultura, convertida para BRL/saca.
    Estrutura: {puts, vencimentos, vencimento, cotacao_brl, cambio}
    Cada put: {strike_brl, premio_brl, volume, open_interest, iv}
    iv está em percentual (ex: 32.0 = 32%).
    Cacheia 1h por (cultura, vencimento).
    """
    if cultura not in TICKER_CME:
        return _RESULTADO_VAZIO.copy()

    # Câmbio
    cambio_cached = cache.get('chain_cambio_brl')
    if cambio_cached is not None:
        cambio = Decimal(str(cambio_cached))
    else:
        import yfinance as yf
        brl = yf.download("USDBRL=X", period="3d", progress=False, auto_adjust=True)
        brl_close = brl['Close'].dropna()
        if brl_close.empty:
            return _RESULTADO_VAZIO.copy()
        cambio = Decimal(str(float(brl_close.iloc[-1])))
        cache.set('chain_cambio_brl', str(cambio), 3600)

    # Cotação atual em BRL
    cotacao_brl = get_cotacao_com_variacao()['cotacao']

    # Lista de vencimentos disponíveis (cacheada separadamente)
    venc_cache_key = f'vencimentos_cme_{cultura}'
    vencimentos = cache.get(venc_cache_key)
    if vencimentos is None:
        import yfinance as yf
        ticker = yf.Ticker(TICKER_CME[cultura])
        vencimentos = list(ticker.options)
        if not vencimentos:
            return {**_RESULTADO_VAZIO.copy(), 'cotacao_brl': cotacao_brl, 'cambio': cambio}
        cache.set(venc_cache_key, vencimentos, 3600)

    venc_real = vencimento if vencimento in vencimentos else vencimentos[0]

    # Puts para o vencimento selecionado
    puts_cache_key = f'chain_puts_{cultura}_{venc_real}'
    puts_cached = cache.get(puts_cache_key)
    if puts_cached is not None:
        return {
            'puts': puts_cached, 'vencimentos': vencimentos,
            'vencimento': venc_real, 'cotacao_brl': cotacao_brl, 'cambio': cambio,
        }

    import yfinance as yf
    ticker = yf.Ticker(TICKER_CME[cultura])
    chain = ticker.option_chain(venc_real)
    puts_df = chain.puts.fillna({'volume': 0, 'openInterest': 0, 'impliedVolatility': 0.35})

    # Filtrar liquidez
    puts_df = puts_df[(puts_df['volume'] > 0) | (puts_df['openInterest'] > 0)]

    # Conversão cents/bushel → BRL/saca
    fator = _SACA_POR_BUSHEL * cambio / 100

    puts = []
    for _, row in puts_df.iterrows():
        strike_cents = Decimal(str(float(row['strike'])))
        premio_cents = Decimal(str(float(row.get('lastPrice', 0) or row.get('bid', 0) or 0)))
        iv_decimal = float(row.get('impliedVolatility', 0.35) or 0.35)
        puts.append({
            'strike_brl':    (strike_cents * fator).quantize(Decimal('0.01')),
            'premio_brl':    (premio_cents * fator).quantize(Decimal('0.01')),
            'volume':        int(float(row.get('volume', 0) or 0)),
            'open_interest': int(float(row.get('openInterest', 0) or 0)),
            'iv':            round(iv_decimal * 100, 1),
        })

    cache.set(puts_cache_key, puts, 3600)
    return {
        'puts': puts, 'vencimentos': vencimentos,
        'vencimento': venc_real, 'cotacao_brl': cotacao_brl, 'cambio': cambio,
    }
```

- [ ] **Step 4: Rodar os testes para confirmar que passam**

```bash
python manage.py test apps.hedge.tests.GetChainOpcoesTestCase -v 2
```

Esperado: `Ran 3 tests ... OK`

- [ ] **Step 5: Commit**

```bash
git add apps/posicao/services.py apps/hedge/tests.py
git commit -m "feat: get_chain_opcoes — chain de puts CME em BRL/saca"
```

---

## Task 2: `_selecionar_cards`, `black_scholes_delta_put`, `black_scholes_theta_put_dia` em `apps/hedge/services.py`

**Files:**
- Modify: `apps/hedge/services.py`
- Modify: `apps/hedge/tests.py`

---

- [ ] **Step 1: Escrever os testes RED**

Adicionar ao final de `apps/hedge/tests.py`:

```python
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
```

- [ ] **Step 2: Rodar para confirmar que falham**

```bash
python manage.py test apps.hedge.tests.SelecionarCardsTestCase apps.hedge.tests.BlackScholesDeltaThetaTestCase -v 2
```

Esperado: `ImportError` — funções não existem.

- [ ] **Step 3: Implementar as 3 funções em `apps/hedge/services.py`**

Adicionar ao final do arquivo (após `simular_estrategias`):

```python
def _selecionar_cards(puts: list, custo: Decimal, cotacao: Decimal) -> list:
    """Seleciona 3 puts representativos: mínima, custo (break-even) e total (ATM)."""
    if not puts:
        return []

    def _mais_proximo(alvo):
        return min(puts, key=lambda p: abs(p['strike_brl'] - alvo))

    card_minima = _mais_proximo(custo * Decimal('0.90'))
    card_custo  = _mais_proximo(custo)
    card_total  = _mais_proximo(cotacao)

    return [
        {'nome': 'Proteção Mínima',   'destaque': False, **card_minima},
        {'nome': 'Proteção do Custo', 'destaque': True,  **card_custo},
        {'nome': 'Proteção Total',    'destaque': False, **card_total},
    ]


def black_scholes_delta_put(
    S: Decimal, K: Decimal, T_anos: Decimal,
    r: float = 0.105, sigma: float = 0.35
) -> float:
    """Delta do put: entre -1.0 e 0.0. Negativo indica queda de preço beneficia o put."""
    S_f, K_f, T_f = float(S), float(K), float(T_anos)
    if T_f <= 0 or sigma <= 0 or S_f <= 0 or K_f <= 0:
        return -1.0 if K_f > S_f else 0.0
    d1 = (log(S_f / K_f) + (r + 0.5 * sigma ** 2) * T_f) / (sigma * sqrt(T_f))
    return round(_norm_cdf(d1) - 1.0, 4)


def black_scholes_theta_put_dia(
    S: Decimal, K: Decimal, T_anos: Decimal,
    r: float = 0.105, sigma: float = 0.35
) -> float:
    """Theta diário do put em R$/saca. Negativo = o put perde valor a cada dia."""
    from math import pi
    S_f, K_f, T_f = float(S), float(K), float(T_anos)
    if T_f <= 0 or sigma <= 0 or S_f <= 0 or K_f <= 0:
        return 0.0
    d1 = (log(S_f / K_f) + (r + 0.5 * sigma ** 2) * T_f) / (sigma * sqrt(T_f))
    d2 = d1 - sigma * sqrt(T_f)
    n_d1 = exp(-d1 * d1 / 2) / sqrt(2 * pi)
    theta_anual = -S_f * n_d1 * sigma / (2 * sqrt(T_f)) + r * K_f * exp(-r * T_f) * _norm_cdf(-d2)
    return round(theta_anual / 365, 4)
```

- [ ] **Step 4: Rodar os testes para confirmar que passam**

```bash
python manage.py test apps.hedge.tests.SelecionarCardsTestCase apps.hedge.tests.BlackScholesDeltaThetaTestCase -v 2
```

Esperado: `Ran 6 tests ... OK`

- [ ] **Step 5: Commit**

```bash
git add apps/hedge/services.py apps/hedge/tests.py
git commit -m "feat: _selecionar_cards, delta e theta para put (Black-Scholes)"
```

---

## Task 3: View `opcoes` + URL + testes de view

**Files:**
- Modify: `apps/hedge/urls.py`
- Modify: `apps/hedge/views.py`
- Modify: `apps/hedge/tests.py`

---

- [ ] **Step 1: Escrever os 4 testes RED**

Adicionar ao final de `apps/hedge/tests.py`:

```python
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
```

- [ ] **Step 2: Rodar para confirmar que falham**

```bash
python manage.py test apps.hedge.tests.OpcoesViewTestCase -v 2
```

Esperado: `NoReverseMatch` — URL não existe ainda.

- [ ] **Step 3: Adicionar URL em `apps/hedge/urls.py`**

Substituir o conteúdo inteiro por:

```python
from django.urls import path
from . import views

app_name = "hedge"

urlpatterns = [
    path("", views.hedge_redirect, name="redirect"),
    path("<int:safra_id>/cenarios/", views.cenarios, name="cenarios"),
    path("<int:safra_id>/proteger/", views.proteger, name="proteger"),
    path("<int:safra_id>/estrategias/", views.estrategias, name="estrategias"),
    path("<int:safra_id>/opcoes/", views.opcoes, name="opcoes"),
]
```

- [ ] **Step 4: Implementar a view `opcoes` em `apps/hedge/views.py`**

Adicionar imports no topo do arquivo (junto aos imports existentes):

```python
import json
from datetime import datetime, date as date_type
```

Adicionar ao import de posicao/services:

```python
from apps.posicao.services import calcular_posicao, get_cotacao_atual, get_historico_cotacao, get_chain_opcoes
```

Adicionar ao import de .services:

```python
from .services import (
    calcular_volatilidade_historica, simular_cenarios, simular_estrategias,
    _selecionar_cards, black_scholes_delta_put, black_scholes_theta_put_dia,
)
```

Adicionar a view ao final do arquivo:

```python
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
        'safra':             safra,
        'posicao':           posicao,
        'cultura_disponivel': True,
        'cards':             cards,
        'cards_json':        cards_json,
        'puts':              chain['puts'],
        'vencimentos_fmt':   vencimentos_fmt,
        'vencimento':        chain['vencimento'],
        'cotacao_brl':       cotacao,
        'card_destaque':     card_destaque,
        'has_greeks':        has_greeks,
    })
```

- [ ] **Step 5: Rodar os testes para confirmar que passam**

```bash
python manage.py test apps.hedge.tests.OpcoesViewTestCase -v 2
```

Esperado: `Ran 4 tests ... OK`

- [ ] **Step 6: Rodar todos os testes**

```bash
python manage.py test
```

Esperado: `Ran 159 tests ... OK`

- [ ] **Step 7: Commit**

```bash
git add apps/hedge/urls.py apps/hedge/views.py apps/hedge/tests.py
git commit -m "feat: view opcoes — chain CME com cards, greeks e simulador"
```

---

## Task 4: Template `opcoes.html` + botões de navegação

**Files:**
- Create: `templates/hedge/opcoes.html`
- Modify: `templates/hedge/cenarios.html`
- Modify: `templates/hedge/estrategias.html`

---

- [ ] **Step 1: Criar `templates/hedge/opcoes.html`**

```html
{% extends "base.html" %}
{% block content %}
<div class="md:ml-60 min-h-screen bg-gray-50">
  <div class="max-w-2xl mx-auto px-4 py-6 pb-24">

    <!-- Cabeçalho -->
    <div class="mb-2">
      <a href="{% url 'hedge:cenarios' safra.id %}"
         class="text-sm text-green-700 hover:underline">← Cenários</a>
    </div>
    <h1 class="text-2xl font-bold text-gray-900 mb-1">
      Proteção de Preço — {{ safra.get_cultura_display }}
    </h1>

    <!-- Contexto do produtor -->
    <div class="bg-white rounded-xl border border-gray-200 p-4 mb-6">
      <p class="text-gray-700">
        Você tem <strong class="text-gray-900">{{ posicao.sacas_a_vender|floatformat:0 }} sacas</strong>
        expostas ao mercado.<br>
        Seu custo é <strong class="text-gray-900">R$ {{ safra.custo_por_saca }}/sc</strong>
        — abaixo disso você tem prejuízo.
      </p>
    </div>

    {% if not cultura_disponivel %}
    <!-- Cultura sem suporte -->
    <div class="bg-yellow-50 border border-yellow-200 rounded-xl p-4">
      <p class="text-yellow-800 font-medium">Opções não disponíveis</p>
      <p class="text-yellow-700 text-sm mt-1">
        Não encontramos contratos de opções para {{ safra.get_cultura_display }}
        na bolsa CME neste momento.
      </p>
    </div>

    {% else %}

    <!-- Chips de vencimento -->
    <div class="mb-6">
      <p class="text-sm font-medium text-gray-600 mb-2">Escolha o vencimento do contrato:</p>
      <div class="flex flex-wrap gap-2">
        {% for v in vencimentos_fmt %}
        <a href="?venc={{ v.value }}"
           class="px-4 py-1.5 rounded-full text-sm font-medium transition-colors
                  {% if v.value == vencimento %}bg-green-700 text-white{% else %}bg-white border border-gray-300 text-gray-700 hover:bg-gray-50{% endif %}">
          {{ v.label }}
        </a>
        {% endfor %}
      </div>
    </div>

    {% if cards %}
    <!-- Título dos cards -->
    <h2 class="text-base font-semibold text-gray-800 mb-3">
      Escolha seu nível de proteção
    </h2>

    <!-- 3 cards de proteção -->
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-6">
      {% for card in cards %}
      <div id="card-{{ forloop.counter0 }}"
           onclick="selecionarCard({{ forloop.counter0 }}, this)"
           class="bg-white rounded-xl p-4 border-2 cursor-pointer transition-all hover:shadow-md
                  {% if card.destaque %}border-green-500{% else %}border-gray-200{% endif %}">

        {% if card.destaque %}
        <div class="text-xs font-bold text-green-600 uppercase tracking-wide mb-2">
          Recomendado para você
        </div>
        {% endif %}

        <h3 class="font-bold text-gray-900 text-sm mb-3">{{ card.nome }}</h3>

        <div class="space-y-2 text-sm">
          <div class="flex justify-between items-center">
            <span class="text-gray-500">Preço garantido</span>
            <span class="font-semibold text-gray-900">R$ {{ card.strike_brl }}/sc</span>
          </div>
          <div class="flex justify-between items-center">
            <span class="text-gray-500">Custo do seguro</span>
            <span class="font-semibold text-orange-600">R$ {{ card.premio_brl }}/sc</span>
          </div>
          <div class="flex justify-between items-center border-t border-gray-100 pt-2">
            <span class="text-gray-500 text-xs">Safra toda</span>
            <span class="font-semibold text-xs">R$ {{ card.custo_total_safra|floatformat:0 }}</span>
          </div>
        </div>

        <div class="mt-3 pt-2 border-t border-gray-100">
          <p class="text-xs text-gray-500">Se o preço cair 25%:</p>
          <p class="text-xs font-medium text-gray-800 mt-0.5">{{ card.cenario_queda }}</p>
        </div>
      </div>
      {% endfor %}
    </div>
    {% endif %}

    <!-- Simulador -->
    <div class="bg-white rounded-xl border border-gray-200 p-4 mb-6">
      <h2 class="font-bold text-gray-900 mb-4">Calcule o custo da sua proteção</h2>

      <div class="mb-4">
        <label class="block text-sm font-medium text-gray-700 mb-1">
          Sacas que você quer proteger
        </label>
        <input type="number" id="sacas-input"
               value="{{ posicao.sacas_a_vender|floatformat:0 }}"
               min="1" max="{{ posicao.sacas_totais|floatformat:0 }}"
               class="w-full border border-gray-300 rounded-lg px-3 py-2 text-gray-900 focus:ring-2 focus:ring-green-500 focus:outline-none"
               oninput="calcularSimulador()">
        <p class="text-xs text-gray-400 mt-1">
          Você tem {{ posicao.sacas_a_vender|floatformat:0 }} sacas ainda sem proteção.
        </p>
      </div>

      <div id="simulador-resultado" class="bg-gray-50 rounded-lg p-3 text-sm space-y-2 text-gray-700">
        <p class="text-gray-400 text-xs">Selecione um nível de proteção acima para simular.</p>
      </div>
    </div>

    <!-- Seção avançada -->
    <details class="bg-white rounded-xl border border-gray-200">
      <summary class="px-4 py-3 font-medium text-gray-700 cursor-pointer select-none hover:bg-gray-50 rounded-xl">
        Para quem quer entender mais ▸
      </summary>
      <div class="px-4 pb-4">
        <p class="text-sm text-gray-500 mt-2 mb-3">
          Esses dados são para quem já conhece um pouco de opções e quer mais detalhe.
        </p>

        <!-- Tabela completa de puts -->
        {% if puts %}
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="text-left text-xs text-gray-500 border-b border-gray-200">
                <th class="pb-2 pr-3">Preço garantido</th>
                <th class="pb-2 pr-3">Custo/sc</th>
                <th class="pb-2 pr-3"
                    title="Quanto o mercado acha que o preço pode oscilar nos próximos meses. Quanto maior, mais caro o seguro.">
                  Nervosismo ℹ
                </th>
                <th class="pb-2"
                    title="Quantos contratos estão ativos no mercado. Quanto maior, mais fácil de comprar e vender.">
                  Interesse ℹ
                </th>
              </tr>
            </thead>
            <tbody>
              {% for put in puts %}
              <tr class="border-b border-gray-50 hover:bg-gray-50">
                <td class="py-2 pr-3 font-medium">R$ {{ put.strike_brl }}</td>
                <td class="py-2 pr-3 text-orange-600">R$ {{ put.premio_brl }}</td>
                <td class="py-2 pr-3 text-gray-600">
                  {{ put.iv }}% <span class="text-xs text-gray-400">{{ put.iv_label }}</span>
                </td>
                <td class="py-2 text-gray-500">{{ put.open_interest|default:"—" }}</td>
              </tr>
              {% endfor %}
            </tbody>
          </table>
        </div>
        {% endif %}

        <!-- Greeks explicados -->
        {% if has_greeks %}
        <div class="mt-5 space-y-3">
          <p class="text-sm font-medium text-gray-700">
            Como o seguro de "{{ card_destaque.nome }}" se comporta:
          </p>

          <div class="bg-blue-50 rounded-lg p-3 text-sm">
            <p class="font-medium text-blue-900">Sensibilidade ao preço (Delta)</p>
            <p class="text-blue-700 mt-1">
              Delta = {{ card_destaque.delta }}
            </p>
            <p class="text-blue-600 text-xs mt-1">
              Se a {{ safra.get_cultura_display }} cair R$ 1/sc, seu seguro ganha cerca de
              R$ {{ card_destaque.delta_abs }}/saca de valor.
            </p>
          </div>

          <div class="bg-orange-50 rounded-lg p-3 text-sm">
            <p class="font-medium text-orange-900">Custo do tempo (Theta)</p>
            <p class="text-orange-700 mt-1">
              Theta = −R$ {{ card_destaque.theta_dia }}/sc/dia
            </p>
            <p class="text-orange-600 text-xs mt-1">
              A cada dia que passa sem o preço cair, seu seguro perde aproximadamente
              R$ {{ card_destaque.theta_dia }}/saca de valor. Quanto mais próximo do vencimento, mais rápido isso acontece.
            </p>
          </div>
        </div>
        {% endif %}
      </div>
    </details>

    {% endif %}{# cultura_disponivel #}

  </div>
</div>

<script>
const cardsData = {{ cards_json|safe }};
const cotacao = parseFloat("{{ cotacao_brl }}");
const custo   = parseFloat("{{ safra.custo_por_saca }}");
let cardIdx = 1;

function selecionarCard(idx, el) {
  cardIdx = idx;
  document.querySelectorAll('[id^="card-"]').forEach(c => {
    c.classList.remove('ring-2', 'ring-green-400');
  });
  el.classList.add('ring-2', 'ring-green-400');
  calcularSimulador();
}

function fmt(val) {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency', currency: 'BRL', maximumFractionDigits: 0
  }).format(val);
}

function calcularSimulador() {
  const sacas = parseFloat(document.getElementById('sacas-input').value) || 0;
  const card  = cardsData[cardIdx];
  if (!card || sacas <= 0) return;

  const strike = card.strike_brl;
  const premio = card.premio_brl;

  const custoTotal  = sacas * premio;
  const lucroIgual  = sacas * (cotacao - custo - premio);
  const precoQueda  = cotacao * 0.80;
  const lucroQueda  = sacas * (Math.max(precoQueda, strike) - custo - premio);
  const precoAlta   = cotacao * 1.15;
  const lucroAlta   = sacas * (precoAlta - custo - premio);

  const queda_cls = lucroQueda >= 0 ? 'text-green-700' : 'text-red-600';
  const queda_txt = lucroQueda >= 0
    ? `você ainda lucra ${fmt(lucroQueda)}`
    : `você perde ${fmt(Math.abs(lucroQueda))}`;

  document.getElementById('simulador-resultado').innerHTML = `
    <div class="flex justify-between">
      <span>Custo total do seguro:</span>
      <strong class="text-orange-600">${fmt(custoTotal)}</strong>
    </div>
    <div class="flex justify-between border-t border-gray-200 pt-2">
      <span>Se o preço ficar igual (R$ ${cotacao.toFixed(0)}/sc):</span>
      <strong>${fmt(lucroIgual)}</strong>
    </div>
    <div class="flex justify-between">
      <span>Se o preço cair 20%:</span>
      <strong class="${queda_cls}">${queda_txt}</strong>
    </div>
    <div class="flex justify-between">
      <span>Se o preço subir 15%:</span>
      <strong class="text-green-700">você lucra ${fmt(lucroAlta)}</strong>
    </div>
    <p class="text-xs text-gray-400 pt-2 border-t border-gray-100">
      O seguro custa ${fmt(custoTotal)} — em qualquer cenário, esse valor já foi pago.
    </p>
  `;
}

document.addEventListener('DOMContentLoaded', () => {
  const cardEl = document.getElementById('card-1');
  if (cardEl) cardEl.classList.add('ring-2', 'ring-green-400');
  calcularSimulador();
});
</script>
{% endblock %}
```

- [ ] **Step 2: Adicionar botão "Ver Opções" em `templates/hedge/cenarios.html`**

Localizar o bloco onde termina a página (antes do `{% endblock %}`) e adicionar antes dele:

```html
    <!-- Botão para opções reais -->
    <div class="mt-6 text-center">
      <a href="{% url 'hedge:opcoes' safra.id %}"
         class="inline-flex items-center gap-2 bg-green-700 text-white px-5 py-2.5 rounded-xl font-medium hover:bg-green-800 transition-colors">
        Ver Opções Disponíveis no Mercado →
      </a>
      <p class="text-xs text-gray-400 mt-2">Veja os preços reais de proteção disponíveis hoje</p>
    </div>
```

- [ ] **Step 3: Adicionar botão "Ver Opções" em `templates/hedge/estrategias.html`**

Mesmo padrão — adicionar antes do `{% endblock %}`:

```html
    <!-- Botão para opções reais -->
    <div class="mt-6 text-center">
      <a href="{% url 'hedge:opcoes' safra.id %}"
         class="inline-flex items-center gap-2 border border-green-700 text-green-700 px-5 py-2.5 rounded-xl font-medium hover:bg-green-50 transition-colors">
        Ver Opções Reais Disponíveis →
      </a>
      <p class="text-xs text-gray-400 mt-2">Compare as estratégias simuladas com os contratos reais do mercado</p>
    </div>
```

- [ ] **Step 4: Rodar todos os testes**

```bash
python manage.py test
```

Esperado: `Ran 159 tests ... OK`

- [ ] **Step 5: Commit**

```bash
git add templates/hedge/opcoes.html templates/hedge/cenarios.html templates/hedge/estrategias.html
git commit -m "feat: template opcoes com cards, simulador JS e seção avançada"
```

---

## Contagem final

| Fase | Testes novos | Total |
|------|-------------|-------|
| Baseline | — | 149 |
| Task 1 (get_chain_opcoes) | +3 | 152 |
| Task 2 (cards, delta, theta) | +6 | 158 |
| Task 3 (view) | +4 | 162 |
| **Total Fase 8** | **+13** | **162** |

> A spec previa 10 testes (+3 de delta/theta foram adicionados no Task 2 por completude).
