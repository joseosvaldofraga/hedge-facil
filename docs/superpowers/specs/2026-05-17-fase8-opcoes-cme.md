# HedgeFácil — Fase 8: Módulo de Opções CME

**Data:** 2026-05-17
**Objetivo:** Mostrar opções reais de commodities agrícolas (CME via yfinance) em linguagem de produtor rural. Tabela de strikes + simulador de custo total + seção avançada opcional.

---

## Contexto

O sistema já usa yfinance para cotação da soja (ZS=F + USDBRL=X). A mesma lib expõe chains completas de opções para ZS (soja), ZC (milho) e KC (café) com ~15 min de atraso — sem API key, sem dependência nova.

O produtor não é trader. Ele quer saber: **quanto custa me proteger** e **o que acontece se o preço cair**. Toda linguagem financeira é traduzida para o mundo dele.

---

## 1. Arquitetura

Nova view `opcoes` no app `hedge`, acessada via `/hedge/<id>/opcoes/`.
Novo serviço `get_chain_opcoes(cultura, vencimento)` em `apps/posicao/services.py` (junto com `get_cotacao_com_variacao` — mesma responsabilidade: dados de mercado).
Função auxiliar `_selecionar_cards(puts, custo)` em `apps/hedge/services.py` (lógica de seleção de estratégia, não dados de mercado).
Sem novos models. Sem novas dependências.

### Mapeamento de cultura → ticker CME

```python
TICKER_CME = {
    "soja":  "ZS=F",
    "milho": "ZC=F",
    "cafe":  "KC=F",
}
```

Culturas sem mapeamento (cana, trigo) mostram aviso "Opções não disponíveis para esta cultura via CME".

> **Nota:** Para KC=F (café), a disponibilidade de chain de opções via yfinance pode ser limitada. Se `ticker.options` retornar lista vazia, a view exibe o mesmo aviso de cultura não disponível.

### Serviço `get_chain_opcoes`

```python
def get_chain_opcoes(cultura: str, vencimento: str) -> dict:
    """
    Retorna {
        'puts': [{'strike_brl': Decimal, 'premio_brl': Decimal, 'volume': int, 'iv': float}, ...],
        'vencimentos': ['2026-03-21', '2026-05-14', ...],
        'cotacao_brl': Decimal,
        'cambio': Decimal,
    }
    Filtra apenas puts. Converte USD/bushel → BRL/saca.
    Cacheia 1h por (cultura, vencimento).
    """
```

Conversão: `preco_brl_saca = preco_usd_bushel * (60/27.2155) * cambio`
— mesma fórmula já em uso no painel.

Filtro de liquidez: exclui puts com `volume == 0 AND openInterest == 0`.

---

## 2. URL

```
app_name = 'hedge' (já existe)

'<int:safra_id>/opcoes/'  → opcoes (GET)
```

Parâmetro GET opcional: `?venc=YYYY-MM-DD` (default: primeiro vencimento disponível).

Montar em `apps/hedge/urls.py` ao lado das rotas existentes.

---

## 3. View `opcoes`

```python
@login_required
def opcoes(request, safra_id):
    safra = get_object_or_404(Safra, id=safra_id, produtor=request.user)
    posicao = calcular_posicao(safra)
    cultura = safra.cultura

    chain = get_chain_opcoes(cultura, vencimento_selecionado)

    # Seleciona 3 cards de proteção ancorados no custo da safra
    custo = safra.custo_por_saca
    cards = _selecionar_cards(chain['puts'], custo)

    return render(request, 'hedge/opcoes.html', {
        'safra': safra,
        'posicao': posicao,
        'cards': cards,
        'puts': chain['puts'],
        'vencimentos': chain['vencimentos'],
        'vencimento': vencimento_selecionado,
        'cotacao_brl': chain['cotacao_brl'],
        'cultura_disponivel': cultura in TICKER_CME,
    })
```

### Lógica `_selecionar_cards`

Seleciona 3 puts da chain para os cards:
- **Proteção Mínima:** put com strike mais próximo de `custo * 0.90`
- **Proteção do Custo:** put com strike mais próximo de `custo` (preço de ruína)
- **Proteção Total:** put ATM — strike mais próximo da cotação atual

---

## 4. Template `templates/hedge/opcoes.html`

### Cabeçalho de contexto

```
Você tem {sacas_a_vender} sacas de {cultura} ainda expostas.
Seu custo é R$ {custo}/sc — abaixo disso você tem prejuízo.
```

### Seção 1 — Vencimento

Chips com label de safra: "Março 2026", "Maio 2026", "Julho 2026".
GET param `?venc=` atualiza a página ao clicar.

### Seção 2 — Três cards de proteção

Cada card mostra:
- Nome: "Proteção Mínima" / "Proteção do Custo" / "Proteção Total"
- **Preço garantido:** R$ XX/sc
- **Custo do seguro:** R$ XX/sc
- **Para proteger sua safra toda:** R$ XXXX
- **Se o preço cair 25%:** "Você perde R$ X" ou "Você fica no zero" ou "Você ainda lucra R$ X"
- **Se o preço subir:** "Você vende normalmente, menos o custo do seguro"

O card "Proteção do Custo" tem destaque visual (borda verde).

### Seção 3 — Simulador

Dois inputs:
- Sacas a proteger (number, default = `posicao.sacas_a_vender`)
- Card selecionado (radio, default = "Proteção do Custo")

Output calculado no cliente (JS simples):
```
Custo total do seguro: R$ XXXX
Se o preço ficar igual:  você lucra R$ XXXX
Se o preço cair 20%:    você fica no zero (custo coberto)
Se o preço subir 15%:   você lucra R$ XXXX + o seguro custou R$ XXXX
```

Sem chamadas ao servidor — tudo calculado com os dados já na página.

### Seção 4 — Avançado (expansível, fechado por padrão)

Título: **"Para quem quer entender mais"** — `<details>` HTML nativo.

Dentro, tabela completa de puts com:

| Preço garantido | Custo/sc | Nervosismo do mercado | Interesse aberto |
|---|---|---|---|
| R$ 110 | R$ 1,80 | 28% — mercado calmo | 1.240 contratos |
| R$ 120 | R$ 3,40 | 32% — mercado moderado | 4.820 contratos |

Tooltips explicativos (title= HTML):
- **Nervosismo do mercado** (= volatilidade implícita): "Quanto o mercado acha que o preço pode oscilar nos próximos meses. Quanto maior, mais caro o seguro."
- **Interesse aberto** (= open interest): "Quantos contratos estão ativos no mercado. Quanto maior, mais fácil de comprar e vender."

Seção de greeks com explicação:

> **Delta (sensibilidade ao preço):** Se a soja subir R$ 1, quanto o valor do seu seguro muda? Delta = 0.45 significa que o seguro sobe R$ 0,45 para cada R$ 1 de queda na soja.
>
> **Theta (custo do tempo):** Seu seguro perde valor todo dia que passa sem o preço cair. Com theta = -0.05, você "paga" R$ 0,05/saca por dia só para manter o seguro.

Os greeks não são buscados do yfinance (a lib não os fornece para futuros). São calculados com Black-Scholes já implementado em `apps/hedge/services.py`, usando a IV da chain como sigma.

---

## 5. Navegação

Adicionar botão "Ver Opções Disponíveis" na página de cenários (`hedge/cenarios.html`) e na de estratégias (`hedge/estrategias.html`), linkando para `/hedge/<safra_id>/opcoes/`.

Sidebar: não adiciona item novo — opções é sub-tela de hedge.

---

## 6. Testes (`apps/hedge/tests.py`)

### `GetChainOpcoesTestCase` (3 testes)
- `test_get_chain_opcoes_retorna_estrutura_esperada` — mock do yfinance
- `test_get_chain_opcoes_converte_para_brl` — verifica conversão USD→BRL
- `test_get_chain_opcoes_filtra_sem_liquidez` — exclui volume=0 e OI=0

### `SelecionarCardsTestCase` (3 testes)
- `test_selecionar_cards_retorna_tres_cards`
- `test_card_custo_mais_proximo_do_break_even`
- `test_card_proteção_total_e_atm`

### `OpcoesViewTestCase` (4 testes)
- `test_opcoes_retorna_200`
- `test_opcoes_requer_login`
- `test_opcoes_cultura_sem_suporte_mostra_aviso`
- `test_opcoes_vencimento_default_e_primeiro_disponivel`

---

## 7. Contagem de testes

| Fase | Novos | Total |
|------|-------|-------|
| Baseline | — | 149 |
| Fase 8 | +10 | 159 |

---

## 8. Arquivos criados/modificados

| Arquivo | Ação |
|---------|------|
| `apps/posicao/services.py` | Adicionar `get_chain_opcoes` |
| `apps/hedge/services.py` | Adicionar `_selecionar_cards` |
| `apps/hedge/views.py` | Adicionar view `opcoes` |
| `apps/hedge/urls.py` | Adicionar rota `<id>/opcoes/` |
| `apps/hedge/tests.py` | Adicionar 10 testes |
| `templates/hedge/opcoes.html` | Criar |
| `templates/hedge/cenarios.html` | Adicionar botão "Ver Opções" |
| `templates/hedge/estrategias.html` | Adicionar botão "Ver Opções" |
