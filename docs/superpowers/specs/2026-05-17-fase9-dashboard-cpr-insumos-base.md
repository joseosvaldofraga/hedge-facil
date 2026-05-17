# HedgeFácil — Fase 9: Dashboard Multi-Safra, CPR, Insumos e Base Local

**Data:** 2026-05-17
**Objetivo:** Quatro funcionalidades que completam o ciclo de gestão de preço para o produtor: visão consolidada de todas as safras, simulador de CPR vs mercado, custo de insumos dolarizado e base local.

---

## Contexto

O sistema tem 5 apps (contas, safra, vendas, posicao, hedge), 164 testes, e usa yfinance para cotação CME. O painel atual mostra apenas a safra `ativa=True`. Todas as 4 features desta fase são adições cirúrgicas — sem novos apps, sem novas dependências.

---

## 1. Novos campos no model `Safra`

Uma única migration adiciona 3 campos opcionais:

```python
# apps/safra/models.py
total_insumos_brl = models.DecimalField(
    max_digits=14, decimal_places=2, null=True, blank=True,
    help_text="Custo total de insumos da safra (R$)"
)
pct_insumos_dolar = models.DecimalField(
    max_digits=5, decimal_places=2, null=True, blank=True, default=Decimal("0"),
    help_text="Percentual do custo de insumos atrelado ao dólar (0–100)"
)
preco_referencia_local = models.DecimalField(
    max_digits=10, decimal_places=2, null=True, blank=True,
    help_text="Preço local informado pelo produtor (cooperativa/trader), R$/sc"
)
```

Property auxiliar no model:

```python
@property
def insumos_por_saca(self) -> Decimal:
    if self.total_insumos_brl and self.producao_estimada_sacas > 0:
        return (self.total_insumos_brl / self.producao_estimada_sacas).quantize(Decimal("0.01"))
    return Decimal("0")
```

---

## 2. Formulário `SafraForm` atualizado

Adicionar os 3 novos campos ao form, todos opcionais:

```python
fields = [
    "cultura", "ano_safra", "producao_estimada_sacas", "custo_por_saca",
    "cidade", "estado",
    "total_insumos_brl", "pct_insumos_dolar", "preco_referencia_local",
]
```

No template `safra/nova.html`, agrupá-los numa seção "Dados opcionais" colapsável (`<details>`):
- **Custo total de insumos (R$)** — fertilizantes, defensivos, sementes
- **% dolarizado** — ex: 60% se a maioria é fertilizante importado
- **Preço local de referência (R$/sc)** — preço que a cooperativa ou trader oferece hoje

---

## 3. Dashboard multi-safra (`/painel/`)

### View `posicao/views.py::painel` — nova lógica

```python
@login_required
def painel(request):
    safras_ativas = Safra.objects.filter(produtor=request.user, ativa=True)
    safras_inativas = Safra.objects.filter(produtor=request.user, ativa=False)
    mercado = get_cotacao_com_variacao()
    historico = get_historico_cotacao()
    cotacao = mercado["cotacao"]

    items = []
    for safra in safras_ativas:
        posicao = calcular_posicao(safra)
        risco = calcular_risco(posicao, safra, cotacao)
        base = (safra.preco_referencia_local - cotacao).quantize(Decimal("0.01")) if safra.preco_referencia_local else None
        insumos_cobertos = posicao.receita_travada >= (safra.total_insumos_brl or Decimal("0"))
        items.append({
            "safra": safra, "posicao": posicao, "risco": risco,
            "base": base, "insumos_cobertos": insumos_cobertos,
        })

    # Consolidado (apenas safras ativas, em BRL)
    receita_total = sum(i["posicao"].receita_travada for i in items)
    exposicao_total = sum(i["posicao"].sacas_a_vender * cotacao for i in items)
    custo_total = sum(i["posicao"].custo_total for i in items)

    return render(request, "posicao/painel.html", {
        "mercado": mercado,
        "cotacao": cotacao,
        "historico_json": json.dumps(historico),
        "items": items,
        "safras_inativas": safras_inativas,
        "receita_total": receita_total,
        "exposicao_total": exposicao_total,
        "custo_total": custo_total,
        "sem_safras": not items and not safras_inativas,
    })
```

### Template `posicao/painel.html` — nova estrutura

1. **Widget de mercado** (igual hoje — cotação soja + histórico + variação)
2. **Barra consolidada** (só se houver ≥ 2 safras ativas):
   - Receita total travada: R$ XXX
   - Exposição total: R$ XXX
   - Custo total: R$ XXX
3. **Cards por safra ativa** (loop em `items`):
   - Cabeçalho: cultura + ano_safra + badge "ativa"
   - Barra de progresso: % vendido
   - Métricas: receita travada / custo coberto (✅/❌) / preço médio
   - Se `base` não é None: "Base local: -R$ X/sc" ou "+R$ X/sc"
   - Se `total_insumos_brl`: "Insumos: cobertos ✅" ou "Insumos: descobertos ❌"
   - Botões: "Cenários" → `/hedge/<id>/cenarios/` | "Registrar venda" → `/vendas/<id>/` | "Opções" → `/hedge/<id>/opcoes/` | "CPR" → `/hedge/<id>/cpr/`
4. **Safras anteriores** (colapsável `<details>`, só se houver safras inativas):
   - Lista simples: cultura + ano + sacas vendidas + receita

O painel **não tem mais uma safra "ativa" destacada** — todas as ativas são iguais. O mecanismo `ativar` safra permanece no model/view mas deixa de ser necessário para o painel.

---

## 4. Simulador CPR vs venda spot (`/hedge/<safra_id>/cpr/`)

### URL

```python
path("<int:safra_id>/cpr/", views.simulador_cpr, name="cpr"),
```

### View `hedge/views.py::simulador_cpr`

```python
@login_required
def simulador_cpr(request, safra_id):
    safra = get_object_or_404(Safra, id=safra_id, produtor=request.user)
    cotacao = get_cotacao_atual()
    return render(request, "hedge/cpr.html", {
        "safra": safra,
        "cotacao_atual": float(cotacao),
        "cdi_anual": 14.75,  # % a.a. — referência fixa, exibida no template
    })
```

### Template `hedge/cpr.html`

Inputs (todos editáveis):
- Preço CPR ofertado (R$/sc) — default: `cotacao_atual`
- Prazo (dias) — default: 180
- CDI referência (% a.a.) — default: 14.75, editável pelo usuário

Outputs calculados em JS sem chamada ao servidor:
- **Taxa efetiva da CPR (% a.a.):** `((preco_cpr / cotacao_spot)^(365/prazo) - 1) × 100`
- **Equivalente spot no vencimento:** `cotacao_spot × (1 + cdi/100)^(prazo/365)` — "Para valer a pena esperar, o preço precisaria estar acima de R$ X/sc"
- **Veredicto:** se taxa_cpr > CDI → "CPR vale mais que carregar até o vencimento" | se não → "Esperando no mercado rende mais se o preço subir acima de R$ X/sc"
- **Tabela de breakeven** por cenário de alta do preço spot:

| Alta do preço | Preço no vencimento | CPR ganha mais? |
|---|---|---|
| +0% | R$ 128 | Sim |
| +5% | R$ 134 | Sim |
| +10% | R$ 140 | Não |

(5 linhas: 0%, +5%, +10%, +15%, +20% de variação do spot)

Link de volta para a safra: "← Voltar ao painel".

---

## 5. Custo de insumos dolarizado (no card de cada safra)

Exibido automaticamente no card do painel se `total_insumos_brl` estiver preenchido:

```
Insumos: R$ XX/sc
  Cobertos pelas vendas travadas: ✅ sim / ❌ não (R$ Y/sc descoberto)
  Exposição cambial: R$ Z/sc — se o dólar subir 20%, seus insumos ficam R$ W/sc mais caros
```

Fórmula exposição cambial: `insumos_por_saca × (pct_insumos_dolar / 100) × 0.20`

---

## 6. Base local (no card de cada safra)

Exibida automaticamente no card se `preco_referencia_local` estiver preenchido:

```
Base hoje: -R$ 7/sc
(Preço da cooperativa vs CME — quanto você perde na conversão)
```

Cálculo: `base = preco_referencia_local − cotacao_cme_brl`

Texto auxiliar: "Base positiva = sua cooperativa paga mais que o CME. Base negativa = você recebe menos."

---

## 7. Navegação

- Link "Simular CPR" nos cards do painel (botão outline) e em `hedge/estrategias.html`
- Sidebar: não muda — CPR é sub-tela de hedge

---

## 8. Testes (`apps/hedge/tests.py` e `apps/posicao/tests.py`)

### `SafraInsumoBaseTestCase` (3 testes — `apps/safra/tests.py`)
- `test_insumos_por_saca_calcula_corretamente`
- `test_insumos_por_saca_sem_dados_retorna_zero`
- `test_preco_referencia_local_opcional`

### `PainelMultiSafraTestCase` (4 testes — `apps/posicao/tests.py`)
- `test_painel_exibe_todas_safras_ativas`
- `test_painel_consolida_receita_e_exposicao`
- `test_painel_sem_safras_exibe_cta`
- `test_painel_safras_inativas_em_secao_separada`

### `SimuladorCprTestCase` (3 testes — `apps/hedge/tests.py`)
- `test_cpr_retorna_200`
- `test_cpr_requer_login`
- `test_cpr_passa_cotacao_e_cdi_para_template`

---

## 9. Contagem de testes

| Fase | Novos | Total |
|------|-------|-------|
| Baseline Fase 9 | — | 164 |
| Fase 9 | +10 | 174 |

---

## 10. Arquivos criados/modificados

| Arquivo | Ação |
|---------|------|
| `apps/safra/models.py` | Adicionar 3 campos + property `insumos_por_saca` |
| `apps/safra/migrations/0003_*.py` | Migration automática |
| `apps/safra/forms.py` | Adicionar 3 campos |
| `templates/safra/nova.html` | Seção "Dados opcionais" colapsável |
| `apps/posicao/views.py` | Reescrever `painel` para multi-safra |
| `templates/posicao/painel.html` | Novo layout: cards por safra + consolidado |
| `apps/hedge/views.py` | Adicionar `simulador_cpr` |
| `apps/hedge/urls.py` | Adicionar rota `<id>/cpr/` |
| `templates/hedge/cpr.html` | Criar |
| `templates/hedge/estrategias.html` | Adicionar link CPR |
| `apps/safra/tests.py` | +3 testes |
| `apps/posicao/tests.py` | +4 testes |
| `apps/hedge/tests.py` | +3 testes |
