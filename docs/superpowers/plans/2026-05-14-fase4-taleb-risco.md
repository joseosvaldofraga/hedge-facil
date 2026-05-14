# HedgeFácil Fase 4 — Risco Taleb

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adicionar análise de risco ao painel — preço de ruína, convexidade da posição e Via Negativa — e expandir cenários hedge com fat-tails.

**Architecture:** Novo dataclass `RiscoSafra` + função `calcular_risco()` em `apps/posicao/services.py` (não altera `PosicaoSafra`). Painel recebe `risco` como contexto extra. `opcao_b3` = posição convexa (piso); demais tipos = côncava (trava). `custo_por_saca` da safra = preço de ruína.

**Tech Stack:** Django 6, Tailwind CSS (classes utilitárias inline), `decimal.Decimal`, `dataclasses.dataclass`.

---

## Arquivos modificados

| Arquivo | Ação |
|---------|------|
| `apps/posicao/services.py` | Adiciona `RiscoSafra`, `calcular_risco()` |
| `apps/posicao/views.py` | Passa `risco` ao contexto do painel |
| `apps/posicao/tests.py` | Adiciona `RiscoSafraTestCase` (9 testes) + 2 testes de view |
| `templates/posicao/painel.html` | Adiciona 3 novos blocos de risco |
| `apps/hedge/services.py` | Variações fat-tail (3 → 6 cenários por padrão) |
| `apps/hedge/tests.py` | Atualiza `test_cenarios_contexto_tem_3_cenarios` + 2 novos |
| `tests/test_calculos.py` | Atualiza `test_retorna_3_cenarios_por_padrao` |
| `templates/hedge/cenarios.html` | Destaca cenários abaixo do custo em vermelho |

---

## Task 1: `RiscoSafra` dataclass + `calcular_risco()` (TDD)

**Files:**
- Modify: `apps/posicao/services.py`
- Modify: `apps/posicao/tests.py`

- [ ] **Step 1: Escrever testes que falham**

Read `apps/posicao/tests.py` para ver imports existentes (tem `Produtor`, `Safra`, `get_cotacao_atual`). Adicionar novos imports e nova classe no final do arquivo:

```python
from apps.vendas.models import Venda
from apps.posicao.services import calcular_posicao, calcular_risco, RiscoSafra
```

Adicionar após `PainelViewTestCase`:

```python
class RiscoSafraTestCase(TestCase):
    def setUp(self):
        self.produtor = Produtor.objects.create_user(
            username="risco_user", email="risco@test.com", password="senha123"
        )
        self.safra = Safra.objects.create(
            produtor=self.produtor,
            cultura="soja",
            ano_safra="2025/26",
            producao_estimada_sacas=Decimal("1000"),
            custo_por_saca=Decimal("80"),
        )
        self.cotacao = Decimal("130")

    def _cria_venda(self, sacas, preco, tipo="balcao"):
        return Venda.objects.create(
            safra=self.safra,
            tipo=tipo,
            contraparte="Cargill",
            sacas=Decimal(str(sacas)),
            preco_por_saca=Decimal(str(preco)),
            data_negociacao="2025-03-01",
        )

    def test_risco_preco_ruina_igual_custo_por_saca(self):
        posicao = calcular_posicao(self.safra)
        risco = calcular_risco(posicao, self.safra, self.cotacao)
        self.assertEqual(risco.preco_ruina, Decimal("80.00"))

    def test_risco_margem_seguranca_positiva(self):
        posicao = calcular_posicao(self.safra)
        risco = calcular_risco(posicao, self.safra, self.cotacao)
        self.assertEqual(risco.margem_seguranca, Decimal("50.00"))

    def test_risco_margem_seguranca_negativa(self):
        posicao = calcular_posicao(self.safra)
        risco = calcular_risco(posicao, self.safra, Decimal("70"))
        self.assertEqual(risco.margem_seguranca, Decimal("-10.00"))

    def test_risco_em_zona_critica_quando_cotacao_proxima(self):
        # preco_ruina=80, 80*1.10=88 → cotacao=85 < 88 → zona crítica
        posicao = calcular_posicao(self.safra)
        risco = calcular_risco(posicao, self.safra, Decimal("85"))
        self.assertTrue(risco.em_zona_critica)

    def test_risco_nao_em_zona_critica_quando_seguro(self):
        posicao = calcular_posicao(self.safra)
        risco = calcular_risco(posicao, self.safra, self.cotacao)
        self.assertFalse(risco.em_zona_critica)

    def test_risco_convexidade_concava_sem_opcoes(self):
        self._cria_venda(300, "120", tipo="balcao")
        posicao = calcular_posicao(self.safra)
        risco = calcular_risco(posicao, self.safra, self.cotacao)
        self.assertEqual(risco.convexidade_label, "Côncava")

    def test_risco_convexidade_convexa_so_opcoes(self):
        self._cria_venda(300, "120", tipo="opcao_b3")
        posicao = calcular_posicao(self.safra)
        risco = calcular_risco(posicao, self.safra, self.cotacao)
        self.assertEqual(risco.convexidade_label, "Convexa")

    def test_risco_convexidade_mista(self):
        self._cria_venda(200, "120", tipo="balcao")
        self._cria_venda(100, "125", tipo="opcao_b3")
        posicao = calcular_posicao(self.safra)
        risco = calcular_risco(posicao, self.safra, self.cotacao)
        self.assertEqual(risco.convexidade_label, "Mista")

    def test_risco_exposicao_no_saldo_correto(self):
        # sem vendas: sacas_a_vender=1000, cotacao=130, ruina=80
        # exposicao = 1000 * (130-80) = 50000
        posicao = calcular_posicao(self.safra)
        risco = calcular_risco(posicao, self.safra, self.cotacao)
        self.assertEqual(risco.exposicao_no_saldo, Decimal("50000.00"))
```

- [ ] **Step 2: Rodar RED**

```bash
cd /media/fragatec/SSD/projetos/web/hedgefacil
.venv/bin/python manage.py test apps.posicao.tests.RiscoSafraTestCase
```

Expected: `ImportError: cannot import name 'calcular_risco'` → RED ✓

- [ ] **Step 3: Implementar `RiscoSafra` e `calcular_risco()`**

Read `apps/posicao/services.py` para ver o conteúdo atual. Substituir pelo arquivo completo:

```python
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
```

- [ ] **Step 4: Rodar GREEN**

```bash
.venv/bin/python manage.py test apps.posicao.tests.RiscoSafraTestCase
```

Expected: 9 PASS ✓

- [ ] **Step 5: Rodar suite completa**

```bash
.venv/bin/python manage.py test
```

Expected: 120 testes (111 + 9), todos OK.

- [ ] **Step 6: Commit**

```bash
git add apps/posicao/services.py apps/posicao/tests.py
git commit -m "$(cat <<'EOF'
task 1: RiscoSafra dataclass e calcular_risco com TDD

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: View painel + template (TDD)

**Files:**
- Modify: `apps/posicao/views.py`
- Modify: `apps/posicao/tests.py`
- Modify: `templates/posicao/painel.html`

- [ ] **Step 1: Escrever testes que falham**

Adicionar ao final de `apps/posicao/tests.py`, dentro de `PainelViewTestCase` (ou após a classe — criar novo helper de safra):

```python
class PainelRiscoViewTestCase(TestCase):
    def setUp(self):
        self.produtor = Produtor.objects.create_user(
            username="risco_view", email="riscoview@test.com", password="senha123"
        )
        Safra.objects.create(
            produtor=self.produtor,
            cultura="soja",
            ano_safra="2025/26",
            producao_estimada_sacas=Decimal("1000"),
            custo_por_saca=Decimal("80"),
        )
        self.client.force_login(self.produtor)

    def test_painel_contexto_tem_risco(self):
        response = self.client.get(reverse("posicao:painel"))
        self.assertIn("risco", response.context)

    def test_painel_risco_e_instancia_de_risco_safra(self):
        from apps.posicao.services import RiscoSafra
        response = self.client.get(reverse("posicao:painel"))
        self.assertIsInstance(response.context["risco"], RiscoSafra)
```

- [ ] **Step 2: Rodar RED**

```bash
.venv/bin/python manage.py test apps.posicao.tests.PainelRiscoViewTestCase
```

Expected: `KeyError: 'risco'` → RED ✓

- [ ] **Step 3: Atualizar view**

Read `apps/posicao/views.py`. Substituir a função `painel`:

```python
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from apps.safra.models import Safra
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

(A função `pdf` permanece igual — não altera.)

- [ ] **Step 4: Rodar GREEN**

```bash
.venv/bin/python manage.py test apps.posicao.tests.PainelRiscoViewTestCase
```

Expected: 2 PASS ✓

- [ ] **Step 5: Atualizar `painel.html`**

Substituir o conteúdo completo de `templates/posicao/painel.html`:

```html
{% extends "base.html" %}
{% block conteudo %}

<div class="bg-amber-50 border border-amber-200 rounded-xl p-3 mb-4 flex justify-between items-center">
  <span class="text-sm text-amber-800">Cotação soja hoje</span>
  <span class="font-display font-bold text-amber-900">R$ {{ cotacao }}</span>
</div>

<div class="rounded-xl p-4 mb-4 border {% if risco.em_zona_critica %}bg-red-50 border-red-300{% else %}bg-amber-50 border-amber-200{% endif %}">
  <p class="text-xs font-semibold uppercase tracking-wide mb-1 {% if risco.em_zona_critica %}text-red-700{% else %}text-amber-700{% endif %}">
    {% if risco.em_zona_critica %}⚠ Zona Crítica de Preço{% else %}Exposição no Saldo{% endif %}
  </p>
  <p class="font-display text-2xl font-bold {% if risco.em_zona_critica %}text-red-700{% else %}text-amber-900{% endif %}">
    R$ {{ risco.exposicao_no_saldo }}
  </p>
  <p class="text-xs mt-1 {% if risco.em_zona_critica %}text-red-600{% else %}text-amber-700{% endif %}">
    {{ posicao.sacas_a_vender }} sc × R$ {{ risco.margem_seguranca }}/sc acima do custo
  </p>
  <div class="mt-3">
    <div class="flex justify-between text-xs mb-1 {% if risco.em_zona_critica %}text-red-700{% else %}text-amber-700{% endif %}">
      <span>Custo total coberto pela receita travada</span>
      <span>{{ risco.pct_custo_coberto }}%</span>
    </div>
    <div class="w-full bg-white rounded-full h-2 overflow-hidden">
      <div class="bg-green-500 h-2 rounded-full" style="width: {{ risco.pct_custo_coberto }}%"></div>
    </div>
  </div>
</div>

<div class="mb-6">
  <div class="flex items-center gap-2">
    <p class="text-sm text-slate-500">{{ safra }}</p>
    <a href="{% url 'safra:lista' %}" class="text-xs text-green-600 underline">Trocar</a>
  </div>
  <h1 class="font-display text-4xl font-bold text-green-800">
    R$ {{ posicao.preco_medio_ponderado }}
  </h1>
  <p class="text-sm text-slate-600">preço médio ponderado</p>
</div>

<div class="bg-white rounded-xl p-4 mb-4 shadow-sm">
  <div class="flex justify-between mb-2">
    <span class="text-sm text-slate-600">Vendido</span>
    <span class="font-semibold">{{ posicao.percentual_vendido }}%</span>
  </div>
  <div class="w-full bg-slate-200 rounded-full h-3">
    <div class="bg-green-600 h-3 rounded-full"
         style="width: {{ posicao.percentual_vendido }}%"></div>
  </div>
  <div class="flex justify-between mt-2 text-xs text-slate-500">
    <span>{{ posicao.sacas_vendidas }} sc vendidas</span>
    <span>{{ posicao.sacas_a_vender }} sc a vender</span>
  </div>
</div>

<div class="grid grid-cols-2 gap-3 mb-4">
  <div class="bg-white rounded-xl p-4 shadow-sm">
    <p class="text-xs text-slate-500">Receita travada</p>
    <p class="font-display text-xl font-bold text-green-700">R$ {{ posicao.receita_travada }}</p>
  </div>
  <div class="bg-white rounded-xl p-4 shadow-sm">
    <p class="text-xs text-slate-500">Lucro parcial</p>
    <p class="font-display text-xl font-bold {% if posicao.lucro_travado_parcial >= 0 %}text-green-700{% else %}text-red-600{% endif %}">
      R$ {{ posicao.lucro_travado_parcial }}
    </p>
  </div>
</div>

<div class="bg-white rounded-xl p-4 mb-4 shadow-sm">
  <p class="text-xs text-slate-500 mb-3">Preço de Ruína</p>
  <div class="flex justify-between text-sm py-1 border-b border-slate-100">
    <span class="text-slate-600">Custo de produção</span>
    <span class="font-semibold">R$ {{ risco.preco_ruina }}/sc</span>
  </div>
  <div class="flex justify-between text-sm py-1 border-b border-slate-100">
    <span class="text-slate-600">Cotação atual</span>
    <span class="font-semibold">R$ {{ cotacao }}/sc</span>
  </div>
  <div class="flex justify-between text-sm pt-1">
    <span class="text-slate-600">Margem</span>
    <span class="font-bold {% if risco.margem_seguranca >= 0 %}text-green-700{% else %}text-red-600{% endif %}">
      {% if risco.margem_seguranca >= 0 %}+{% endif %}R$ {{ risco.margem_seguranca }}/sc
    </span>
  </div>
</div>

<div class="bg-white rounded-xl p-4 mb-4 shadow-sm">
  <div class="flex justify-between items-center mb-3">
    <p class="text-xs text-slate-500">Convexidade da Posição</p>
    <span class="text-xs font-semibold px-2 py-1 rounded-full
      {% if risco.convexidade_label == 'Convexa' %}bg-green-100 text-green-700
      {% elif risco.convexidade_label == 'Mista' %}bg-blue-100 text-blue-700
      {% elif risco.convexidade_label == 'Côncava' %}bg-orange-100 text-orange-700
      {% else %}bg-slate-100 text-slate-500{% endif %}">
      {{ risco.convexidade_label }}
    </span>
  </div>
  <div class="space-y-2 text-xs text-slate-600">
    <div class="flex justify-between">
      <span>Preço fixo (balcão/futuro/termo)</span>
      <span class="font-semibold">{{ risco.sacas_travadas }} sc</span>
    </div>
    <div class="flex justify-between">
      <span>Com piso (opção B3)</span>
      <span class="font-semibold">{{ risco.sacas_com_piso }} sc</span>
    </div>
  </div>
</div>

<a href="{% url 'vendas:lista' safra.id %}"
   class="block w-full bg-green-700 text-white text-center rounded-xl py-4 font-semibold min-h-[48px]">
  Ver vendas
</a>
<a href="{% url 'hedge:cenarios' safra.id %}"
   class="block w-full border border-green-700 text-green-700 text-center rounded-xl py-4 font-semibold mt-3 min-h-[48px]">
  Simular cenários
</a>
<a href="{% url 'posicao:pdf' %}"
   class="block w-full border border-slate-400 text-slate-600 text-center rounded-xl py-3 font-semibold mt-3 min-h-[48px] text-sm">
  Baixar PDF
</a>
{% endblock %}
```

- [ ] **Step 6: Rodar suite completa**

```bash
.venv/bin/python manage.py test
```

Expected: 122 testes (120 + 2), todos OK.

- [ ] **Step 7: Commit**

```bash
git add apps/posicao/views.py apps/posicao/tests.py templates/posicao/painel.html
git commit -m "$(cat <<'EOF'
task 2: painel com via negativa, preço de ruína e convexidade

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Cenários fat-tail + destaque visual no hedge

**Files:**
- Modify: `apps/hedge/services.py`
- Modify: `apps/hedge/tests.py`
- Modify: `tests/test_calculos.py`
- Modify: `templates/hedge/cenarios.html`

- [ ] **Step 1: Atualizar teste quebrado em `tests/test_calculos.py`**

Read `tests/test_calculos.py`. Encontrar `test_retorna_3_cenarios_por_padrao` e renomear/atualizar:

```python
def test_retorna_6_cenarios_por_padrao(self):
    cenarios = simular_cenarios(
        sacas_a_vender=Decimal("700"),
        preco_atual=Decimal("130"),
    )
    self.assertEqual(len(cenarios), 6)
```

(renomeia o método — apaga a linha do nome antigo e substitui pelo novo)

- [ ] **Step 2: Adicionar 2 testes novos em `apps/hedge/tests.py`**

Read `apps/hedge/tests.py`. Encontrar `HedgeViewsTestCase`. Atualizar o teste existente e adicionar dois novos:

Substituir `test_cenarios_contexto_tem_3_cenarios`:
```python
def test_cenarios_contexto_tem_6_cenarios(self):
    response = self.client.get(reverse("hedge:cenarios", args=[self.safra.id]))
    self.assertEqual(len(response.context["cenarios"]), 6)
```

Adicionar ao final da classe:
```python
def test_cenarios_incluem_queda_50(self):
    response = self.client.get(reverse("hedge:cenarios", args=[self.safra.id]))
    variacoes = [c.variacao_percentual for c in response.context["cenarios"]]
    self.assertIn(Decimal("-50"), variacoes)

def test_cenarios_incluem_alta_30(self):
    response = self.client.get(reverse("hedge:cenarios", args=[self.safra.id]))
    variacoes = [c.variacao_percentual for c in response.context["cenarios"]]
    self.assertIn(Decimal("30"), variacoes)
```

- [ ] **Step 3: Rodar RED**

```bash
.venv/bin/python manage.py test apps.hedge.tests.HedgeViewsTestCase tests.test_calculos.SimularCenariosTestCase
```

Expected: 3 falhas — os testes de contagem e novos cenários → RED ✓

- [ ] **Step 4: Atualizar `apps/hedge/services.py`**

Read o arquivo. Substituir o conteúdo completo:

```python
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
    Decimal("-50"): "Queda extrema 50%",
    Decimal("-35"): "Queda severa 35%",
    Decimal("-20"): "Queda 20%",
    Decimal("0"):   "Preço estável",
    Decimal("15"):  "Alta 15%",
    Decimal("30"):  "Alta forte 30%",
}


def simular_cenarios(
    sacas_a_vender: Decimal,
    preco_atual: Decimal,
    variacoes: list[Decimal] = None,
) -> list[CenarioPreco]:
    if variacoes is None:
        variacoes = [
            Decimal("-50"), Decimal("-35"), Decimal("-20"),
            Decimal("0"), Decimal("15"), Decimal("30"),
        ]

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
```

- [ ] **Step 5: Rodar GREEN**

```bash
.venv/bin/python manage.py test apps.hedge.tests.HedgeViewsTestCase tests.test_calculos.SimularCenariosTestCase
```

Expected: todos PASS ✓

- [ ] **Step 6: Atualizar `templates/hedge/cenarios.html`**

Read o arquivo. Substituir o bloco `{% for cenario in cenarios %}` pelo seguinte (adiciona destaque vermelho para cenários abaixo do custo):

```html
{% extends "base.html" %}
{% block conteudo %}
<h1 class="font-display text-2xl font-bold text-green-800 mb-2">Cenários de Preço</h1>
<p class="text-sm text-slate-500 mb-4">{{ posicao.sacas_a_vender }} sc a vender · preço atual R$ {{ preco_atual }}</p>

{% for cenario in cenarios %}
<div class="rounded-xl p-4 mb-3 shadow-sm border
  {% if cenario.preco_projetado < safra.custo_por_saca %}
    bg-red-50 border-red-200
  {% else %}
    bg-white border-slate-100
  {% endif %}">
  {% if cenario.preco_projetado < safra.custo_por_saca %}
  <p class="text-xs font-semibold text-red-600 mb-1">⚠ Abaixo do custo de produção</p>
  {% endif %}
  <div class="flex justify-between items-center">
    <span class="font-semibold {% if cenario.preco_projetado < safra.custo_por_saca %}text-red-800{% else %}text-slate-800{% endif %}">
      {{ cenario.nome }}
    </span>
    <span class="font-display text-lg font-bold
      {% if cenario.preco_projetado < safra.custo_por_saca %}text-red-700
      {% elif cenario.impacto_vs_atual > 0 %}text-green-700
      {% elif cenario.impacto_vs_atual < 0 %}text-red-600
      {% else %}text-slate-700{% endif %}">
      R$ {{ cenario.preco_projetado }}
    </span>
  </div>
  <div class="mt-2 text-sm text-slate-600">
    Receita: <strong>R$ {{ cenario.receita_no_saldo }}</strong>
    <span class="ml-2 {% if cenario.impacto_vs_atual > 0 %}text-green-600{% elif cenario.impacto_vs_atual < 0 %}text-red-600{% endif %}">
      ({% if cenario.impacto_vs_atual > 0 %}+{% endif %}R$ {{ cenario.impacto_vs_atual }})
    </span>
  </div>
</div>
{% endfor %}

<a href="{% url 'hedge:proteger' safra.id %}"
   class="block w-full bg-green-700 text-white text-center rounded-xl py-4 font-semibold mt-4 min-h-[48px]">
  Quero me proteger
</a>
{% endblock %}
```

- [ ] **Step 7: Rodar suite completa**

```bash
.venv/bin/python manage.py test
```

Expected: 124 testes (122 + 2), todos OK.

**Nota:** O teste `test_variacoes_customizadas` em `tests/test_calculos.py` passa variações customizadas `["-10", "10"]` e espera `len == 2` — continua válido pois o parâmetro `variacoes` ainda funciona.

- [ ] **Step 8: Commit**

```bash
git add apps/hedge/services.py apps/hedge/tests.py tests/test_calculos.py templates/hedge/cenarios.html
git commit -m "$(cat <<'EOF'
task 3: cenários fat-tail (6 variações), destaque abaixo do custo no hedge

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Verificação final

```bash
.venv/bin/python manage.py test
# Expected: 124 testes, todos OK

.venv/bin/python manage.py check
# Expected: System check identified no issues
```

## Contagem de testes

| Task | Novos/Atualizados | Total |
|------|-------------------|-------|
| Baseline | — | 111 |
| Task 1 (RiscoSafra) | +9 | 120 |
| Task 2 (painel view) | +2 | 122 |
| Task 3 (fat-tail) | +2 novos, 2 renomeados | 124 |
