# HedgeFácil — Fase 4: Risco Taleb (Preço de Ruína, Convexidade, Via Negativa)

**Data:** 2026-05-14
**Objetivo:** Adicionar análise de risco inspirada em Nassim Taleb ao painel — preço de ruína, convexidade da posição e via negativa.

---

## Arquitetura

Padrão B: novo dataclass `RiscoSafra` + função `calcular_risco(posicao, safra, cotacao)` em `apps/posicao/services.py`. Não altera `PosicaoSafra` nem `calcular_posicao()`.

**`custo_por_saca` = preço de ruína.** O produtor já informa o custo all-in ao cadastrar a safra. Sem campo adicional no model.

**`opcao_b3` = posição convexa (piso).** Todos os outros tipos de venda = posição côncava (trava de preço).

---

## 1. `RiscoSafra` dataclass + `calcular_risco()`

**Arquivo:** `apps/posicao/services.py`

```python
@dataclass
class RiscoSafra:
    # Preço de Ruína
    preco_ruina: Decimal          # = safra.custo_por_saca
    margem_seguranca: Decimal     # cotacao - preco_ruina
    pct_custo_coberto: Decimal    # receita_travada / custo_total * 100
    em_zona_critica: bool         # cotacao < preco_ruina * Decimal("1.10")

    # Convexidade
    sacas_travadas: Decimal       # vendas com tipo != opcao_b3
    sacas_com_piso: Decimal       # vendas com tipo == opcao_b3
    pct_convexo: Decimal          # sacas_com_piso / sacas_vendidas * 100 (0 se sem vendas)
    convexidade_label: str        # "Côncava" / "Mista" / "Convexa" / "Sem posição"

    # Via Negativa
    exposicao_no_saldo: Decimal   # sacas_a_vender * (cotacao - preco_ruina)
```

**Regra de convexidade:**
- `sacas_vendidas == 0` → `"Sem posição"`
- `sacas_com_piso == 0` → `"Côncava"`
- `sacas_travadas == 0` → `"Convexa"`
- ambos > 0 → `"Mista"`

**Função:**
```python
def calcular_risco(posicao: PosicaoSafra, safra: Safra, cotacao: Decimal) -> RiscoSafra:
    vendas = safra.vendas.all()
    sacas_com_piso = sum(
        (v.sacas for v in vendas if v.tipo == "opcao_b3"), Decimal("0")
    )
    sacas_travadas = posicao.sacas_vendidas - sacas_com_piso

    if posicao.sacas_vendidas > 0:
        pct_convexo = sacas_com_piso / posicao.sacas_vendidas * 100
    else:
        pct_convexo = Decimal("0")

    if posicao.sacas_vendidas == 0:
        label = "Sem posição"
    elif sacas_com_piso == 0:
        label = "Côncava"
    elif sacas_travadas == 0:
        label = "Convexa"
    else:
        label = "Mista"

    preco_ruina = safra.custo_por_saca
    margem = cotacao - preco_ruina
    pct_coberto = (
        posicao.receita_travada / posicao.custo_total * 100
        if posicao.custo_total > 0
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
```

**Testes (8):**
- `test_risco_preco_ruina_igual_custo_por_saca`
- `test_risco_margem_seguranca_positiva`
- `test_risco_margem_seguranca_negativa`
- `test_risco_em_zona_critica_quando_cotacao_proxima`
- `test_risco_convexidade_concava_sem_opcoes`
- `test_risco_convexidade_convexa_so_opcoes`
- `test_risco_convexidade_mista`
- `test_risco_exposicao_no_saldo_correto`

---

## 2. View `painel` — passa `risco` ao template

**Arquivo:** `apps/posicao/views.py`

```python
from .services import calcular_posicao, calcular_risco, get_cotacao_atual

@login_required
def painel(request):
    safra = Safra.objects.filter(produtor=request.user, ativa=True).first()
    if not safra:
        return redirect("safra:nova")
    posicao = calcular_posicao(safra)
    cotacao = get_cotacao_atual()
    risco = calcular_risco(posicao, safra, cotacao)
    return render(request, "posicao/painel.html", {
        "posicao": posicao,
        "safra": safra,
        "cotacao": cotacao,
        "risco": risco,
    })
```

**Testes (2):**
- `test_painel_contexto_tem_risco`
- `test_painel_risco_e_instancia_de_risco_safra`

---

## 3. Template `painel.html` — 3 novos blocos

Hierarquia visual (mobile-first, Tailwind):

```
[cotação amber — já existe]
[VIA NEGATIVA — novo, topo, cor dinâmica]
[preço médio — já existe]
[barra % vendido — já existe]
[receita travada / lucro — já existe]
[PREÇO DE RUÍNA — novo]
[CONVEXIDADE — novo]
[botões — já existem]
```

### Bloco Via Negativa

Cor do bloco depende de `risco.em_zona_critica`:
- `True` → `bg-red-50 border-red-300`
- `False` → `bg-amber-50 border-amber-200`

Conteúdo:
```
Exposição no saldo: R$ {exposicao_no_saldo}
{sacas_a_vender} sc × (R${cotacao} − R${preco_ruina} custo)

Custo total coberto: {pct_custo_coberto}%
[barra de progresso verde até 100%]
```

### Bloco Preço de Ruína

Card branco com 3 linhas:
```
Preço de ruína    R$ {preco_ruina}/sc
Cotação atual     R$ {cotacao}/sc
Margem            +R$ {margem_seguranca}/sc  [verde] ou -R$ [vermelho]
```

### Bloco Convexidade

Card branco com label badge + duas barras:
```
Posição: [Côncava / Mista / Convexa]  (badge colorido)
▓▓▓▓▓░░  {sacas_travadas} sc travadas (preço fixo)
░░░░░▓▓  {sacas_com_piso} sc com piso (opção B3)
```

Badge cores:
- Côncava → `bg-orange-100 text-orange-700`
- Mista → `bg-blue-100 text-blue-700`
- Convexa → `bg-green-100 text-green-700`
- Sem posição → `bg-slate-100 text-slate-500`

---

## 4. Cenários fat-tail em `hedge/services.py`

**Arquivo:** `apps/hedge/services.py`

Alterar variações padrão:
```python
variacoes = [Decimal("-50"), Decimal("-35"), Decimal("-20"), Decimal("0"), Decimal("15"), Decimal("30")]
```

Nomes padrão correspondentes:
```python
_NOMES_PADRAO = {
    Decimal("-50"): "Queda extrema 50%",
    Decimal("-35"): "Queda severa 35%",
    Decimal("-20"): "Queda 20%",
    Decimal("0"):   "Preço estável",
    Decimal("15"):  "Alta 15%",
    Decimal("30"):  "Alta forte 30%",
}
```

Template `hedge/cenarios.html`: destacar em vermelho os cenários onde `cenario.preco_projetado < risco.preco_ruina`. Para isso, a view de cenários também recebe `risco` no contexto.

**Testes (3):**
- `test_simular_cenarios_retorna_6_por_padrao` (novo)
- `test_cenarios_incluem_queda_50_e_alta_30` (novo)
- `test_retorna_3_cenarios_por_padrao` em `tests/test_calculos.py` → **atualizar** para `assertEqual(len(cenarios), 6)`

Template `hedge/cenarios.html`: a view já passa `safra` ao contexto. Usar `{% if cenario.preco_projetado < safra.custo_por_saca %}` diretamente no template para destacar em vermelho — sem mudança na view.

---

## Arquivos modificados/criados

| Arquivo | Ação |
|---------|------|
| `apps/posicao/services.py` | Adiciona `RiscoSafra`, `calcular_risco()` |
| `apps/posicao/views.py` | Passa `risco` ao painel |
| `apps/posicao/tests.py` | Adiciona 10 testes |
| `templates/posicao/painel.html` | Adiciona 3 blocos |
| `apps/hedge/services.py` | Variações fat-tail |
| `apps/hedge/tests.py` | Atualiza `test_retorna_3_cenarios_por_padrao` + 2 novos |
| `tests/test_calculos.py` | Atualiza `test_retorna_3_cenarios_por_padrao` |
| `templates/hedge/cenarios.html` | Destaca cenários abaixo do custo (usa `safra.custo_por_saca`) |

## Contagem de testes

| Task | Novos | Total |
|------|-------|-------|
| Baseline | — | 111 |
| Task 1 (RiscoSafra + calcular_risco) | 8 | 119 |
| Task 2 (painel view + template) | 2 | 121 |
| Task 3 (fat-tail + hedge view) | 2 | 123 |
