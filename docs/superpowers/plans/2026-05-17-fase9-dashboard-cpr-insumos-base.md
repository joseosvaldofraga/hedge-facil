# Fase 9 — Dashboard Multi-Safra, CPR, Insumos e Base Local

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adicionar 4 funcionalidades ao HedgeFácil: dashboard que exibe todas as safras ativas com totais consolidados, campos opcionais de insumos dolarizados e base local no model Safra, e simulador de CPR vs venda spot.

**Architecture:** Task 1 adiciona campos ao model Safra + migration. Task 2 atualiza form e template nova.html. Task 3 reescreve a view painel para multi-safra, atualiza o template e corrige os 5 testes existentes que quebram. Task 4 cria view/URL/template do simulador CPR. Sem novos apps, sem novas dependências.

**Tech Stack:** Django 6, Python 3.12, Tailwind CSS (CDN), JS vanilla, pytest/Django TestCase. Projeto em `/media/fragatec/SSD/projetos/web/hedgefacil/`. Rodar testes com `python manage.py test`.

---

## Arquivos modificados/criados

| Arquivo | Ação |
|---------|------|
| `apps/safra/models.py` | +3 campos + property `insumos_por_saca` |
| `apps/safra/migrations/0002_*.py` | Migration gerada automaticamente |
| `apps/safra/forms.py` | +3 campos no `SafraForm` |
| `apps/safra/tests.py` | +3 testes |
| `templates/safra/nova.html` | +seção opcional colapsável |
| `apps/posicao/views.py` | Reescrever view `painel` |
| `apps/posicao/tests.py` | Atualizar 5 testes + adicionar 4 novos |
| `templates/posicao/painel.html` | Reescrever para multi-safra |
| `apps/hedge/views.py` | +view `simulador_cpr` |
| `apps/hedge/urls.py` | +rota `<id>/cpr/` |
| `apps/hedge/tests.py` | +3 testes |
| `templates/hedge/cpr.html` | Criar |
| `templates/hedge/estrategias.html` | +link CPR |

---

## Task 1: Campos no model Safra + migration

**Files:**
- Modify: `apps/safra/models.py`
- Modify: `apps/safra/tests.py`
- Create: `apps/safra/migrations/0002_*.py` (gerado automaticamente)

- [ ] **Step 1: Escrever testes para os novos campos**

Adicionar ao final de `apps/safra/tests.py`:

```python
class SafraInsumoBaseTestCase(TestCase):
    def setUp(self):
        self.produtor = Produtor.objects.create_user(
            username="insumo_user", email="insumo@test.com", password="senha123"
        )

    def test_insumos_por_saca_calcula_corretamente(self):
        safra = Safra.objects.create(
            produtor=self.produtor, cultura="soja", ano_safra="2025/26",
            producao_estimada_sacas=Decimal("1000"), custo_por_saca=Decimal("80"),
            total_insumos_brl=Decimal("50000"),
        )
        self.assertEqual(safra.insumos_por_saca, Decimal("50.00"))

    def test_insumos_por_saca_sem_dados_retorna_zero(self):
        safra = Safra.objects.create(
            produtor=self.produtor, cultura="soja", ano_safra="2025/26",
            producao_estimada_sacas=Decimal("1000"), custo_por_saca=Decimal("80"),
        )
        self.assertEqual(safra.insumos_por_saca, Decimal("0"))

    def test_preco_referencia_local_opcional(self):
        safra = Safra.objects.create(
            produtor=self.produtor, cultura="soja", ano_safra="2025/26",
            producao_estimada_sacas=Decimal("1000"), custo_por_saca=Decimal("80"),
            preco_referencia_local=Decimal("125.50"),
        )
        safra.refresh_from_db()
        self.assertEqual(safra.preco_referencia_local, Decimal("125.50"))
```

- [ ] **Step 2: Rodar testes para confirmar falha**

```bash
python manage.py test apps.safra.tests.SafraInsumoBaseTestCase -v 2
```

Esperado: FAIL — `TypeError: Safra() got unexpected keyword arguments: 'total_insumos_brl'`

- [ ] **Step 3: Adicionar campos ao model**

Em `apps/safra/models.py`, adicionar após `ativa` e antes de `criada_em`, e adicionar a property:

```python
from decimal import Decimal
from django.db import models
from django.conf import settings


class Cultura(models.TextChoices):
    SOJA = "soja", "Soja"
    MILHO = "milho", "Milho"
    CAFE = "cafe", "Café"
    CANA = "cana", "Cana-de-açúcar"
    TRIGO = "trigo", "Trigo"


class Safra(models.Model):
    produtor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="safras",
    )
    cultura = models.CharField(max_length=20, choices=Cultura.choices)
    ano_safra = models.CharField(max_length=10, help_text="Ex: 2025/26")
    producao_estimada_sacas = models.DecimalField(max_digits=12, decimal_places=2)
    custo_por_saca = models.DecimalField(max_digits=10, decimal_places=2)
    cidade = models.CharField(max_length=100, blank=True)
    estado = models.CharField(max_length=2, blank=True)
    ativa = models.BooleanField(default=True)
    total_insumos_brl = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True,
        help_text="Custo total de insumos da safra (R$)",
    )
    pct_insumos_dolar = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True, default=Decimal("0"),
        help_text="% do custo de insumos atrelado ao dólar (0–100)",
    )
    preco_referencia_local = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Preço local informado pelo produtor (cooperativa/trader), R$/sc",
    )
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("produtor", "cultura", "ano_safra")]
        ordering = ["-criada_em"]

    def __str__(self):
        return f"{self.get_cultura_display()} {self.ano_safra} — {self.produtor.username}"

    @property
    def custo_total(self) -> Decimal:
        return self.producao_estimada_sacas * self.custo_por_saca

    @property
    def insumos_por_saca(self) -> Decimal:
        if self.total_insumos_brl and self.producao_estimada_sacas > 0:
            return (self.total_insumos_brl / self.producao_estimada_sacas).quantize(Decimal("0.01"))
        return Decimal("0")
```

- [ ] **Step 4: Gerar e aplicar migration**

```bash
python manage.py makemigrations safra
python manage.py migrate
```

Esperado: `Migrations for 'safra': apps/safra/migrations/0002_safra_*.py` + `OK`

- [ ] **Step 5: Rodar testes**

```bash
python manage.py test apps.safra.tests.SafraInsumoBaseTestCase -v 2
```

Esperado: 3 testes PASS

- [ ] **Step 6: Rodar suite completa para confirmar sem regressões**

```bash
python manage.py test
```

Esperado: 167 testes OK (164 + 3 novos)

- [ ] **Step 7: Commit**

```bash
git add apps/safra/models.py apps/safra/migrations/ apps/safra/tests.py
git commit -m "feat: campos insumos e base local no model Safra"
```

---

## Task 2: SafraForm + template nova.html

**Files:**
- Modify: `apps/safra/forms.py`
- Modify: `templates/safra/nova.html`

- [ ] **Step 1: Atualizar SafraForm**

Substituir o conteúdo de `apps/safra/forms.py`:

```python
from django import forms
from .models import Safra


class SafraForm(forms.ModelForm):
    class Meta:
        model = Safra
        fields = [
            "cultura", "ano_safra", "producao_estimada_sacas", "custo_por_saca",
            "cidade", "estado",
            "total_insumos_brl", "pct_insumos_dolar", "preco_referencia_local",
        ]
        widgets = {
            "producao_estimada_sacas": forms.NumberInput(attrs={"placeholder": "Ex: 3000"}),
            "custo_por_saca": forms.NumberInput(attrs={"placeholder": "Ex: 80.00", "step": "0.01"}),
            "ano_safra": forms.TextInput(attrs={"placeholder": "Ex: 2025/26"}),
            "total_insumos_brl": forms.NumberInput(attrs={"placeholder": "Ex: 120000.00", "step": "0.01"}),
            "pct_insumos_dolar": forms.NumberInput(attrs={"placeholder": "Ex: 60", "step": "1", "min": "0", "max": "100"}),
            "preco_referencia_local": forms.NumberInput(attrs={"placeholder": "Ex: 121.50", "step": "0.01"}),
        }
```

- [ ] **Step 2: Adicionar seção opcional ao template nova.html**

Substituir o bloco entre o campo `estado` e o botão submit em `templates/safra/nova.html` — inserir após o `</div>` do grid cidade/estado e antes do botão submit:

```html
  <details class="border border-slate-200 rounded-xl overflow-hidden">
    <summary class="px-4 py-3 text-sm font-medium text-slate-600 cursor-pointer hover:bg-slate-50 select-none">
      Dados opcionais — insumos e preço local
    </summary>
    <div class="px-4 pb-4 pt-3 space-y-4 border-t border-slate-100">
      <p class="text-xs text-slate-500">Preencha para ver se suas vendas já cobrem os insumos e qual é a base local da sua cooperativa.</p>

      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1.5">Custo total de insumos (R$) <span class="text-slate-400 font-normal">opcional</span></label>
          <input type="number" name="total_insumos_brl"
                 value="{{ form.total_insumos_brl.value|default:'' }}"
                 placeholder="Ex: 120000.00" step="0.01" min="0"
                 class="w-full border border-slate-300 rounded-xl px-3 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-green-500">
          {% if form.total_insumos_brl.errors %}<p class="text-red-600 text-xs mt-1">{{ form.total_insumos_brl.errors.0 }}</p>{% endif %}
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1.5">% dolarizado <span class="text-slate-400 font-normal">opcional</span></label>
          <input type="number" name="pct_insumos_dolar"
                 value="{{ form.pct_insumos_dolar.value|default:'' }}"
                 placeholder="Ex: 60" step="1" min="0" max="100"
                 class="w-full border border-slate-300 rounded-xl px-3 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-green-500">
          <p class="text-xs text-slate-400 mt-1">Fertilizantes importados costumam ser ~60%</p>
        </div>
      </div>

      <div>
        <label class="block text-sm font-medium text-slate-700 mb-1.5">Preço local de referência (R$/sc) <span class="text-slate-400 font-normal">opcional</span></label>
        <input type="number" name="preco_referencia_local"
               value="{{ form.preco_referencia_local.value|default:'' }}"
               placeholder="Ex: 121.50" step="0.01" min="0"
               class="w-full border border-slate-300 rounded-xl px-3 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-green-500">
        <p class="text-xs text-slate-400 mt-1">Preço que a cooperativa ou trader está pagando hoje</p>
      </div>
    </div>
  </details>
```

- [ ] **Step 3: Rodar testes existentes de safra para confirmar sem regressões**

```bash
python manage.py test apps.safra -v 2
```

Esperado: todos PASS (os testes de safra existentes não verificam campos opcionais)

- [ ] **Step 4: Commit**

```bash
git add apps/safra/forms.py templates/safra/nova.html
git commit -m "feat: safra form com seção opcional de insumos e base local"
```

---

## Task 3: Dashboard multi-safra

**Files:**
- Modify: `apps/posicao/views.py`
- Modify: `apps/posicao/tests.py`
- Modify: `templates/posicao/painel.html`

**Contexto crítico:** A view `painel` atual coloca `safra`, `posicao` e `risco` diretamente no contexto. A nova versão usa uma lista `items` (uma por safra ativa). Isso **quebra 5 testes existentes** que precisam ser atualizados junto com a nova implementação.

### Testes que quebram (atualizar):
- `PainelViewTestCase.test_painel_contexto_tem_posicao` → verificar `items[0]["posicao"]`
- `PainelViewTestCase.test_painel_contexto_tem_safra` → verificar `items[0]["safra"]`
- `PainelViewTestCase.test_painel_nao_mostra_safra_de_outro_produtor` → verificar `items` vazio
- `PainelRiscoViewTestCase.test_painel_contexto_tem_risco` → verificar `items[0]["risco"]`
- `PainelRiscoViewTestCase.test_painel_risco_e_instancia_de_risco_safra` → verificar `items[0]["risco"]`

- [ ] **Step 1: Atualizar testes existentes e adicionar novos em `apps/posicao/tests.py`**

**Substituir** `PainelViewTestCase` inteira (linhas 12–81) por:

```python
class PainelViewTestCase(TestCase):
    def setUp(self):
        self.produtor = Produtor.objects.create_user(
            username="ze", email="ze@test.com", password="senha123"
        )
        self.client.force_login(self.produtor)
        self.patcher = patch(
            "apps.posicao.views.get_cotacao_com_variacao",
            return_value={
                "cotacao": Decimal("130.00"), "variacao_pct": Decimal("0"),
                "variacao_abs": Decimal("0"), "cambio": Decimal("5.80"), "fonte": "CME/B3",
            },
        )
        self.patcher2 = patch("apps.posicao.views.get_historico_cotacao", return_value=[])
        self.patcher.start()
        self.patcher2.start()

    def tearDown(self):
        self.patcher.stop()
        self.patcher2.stop()

    def _cria_safra(self, cultura="soja", ano="2025/26", ativa=True):
        return Safra.objects.create(
            produtor=self.produtor, cultura=cultura, ano_safra=ano,
            producao_estimada_sacas=Decimal("1000"), custo_por_saca=Decimal("80"), ativa=ativa,
        )

    def test_painel_requer_login(self):
        self.client.logout()
        response = self.client.get(reverse("posicao:painel"))
        self.assertEqual(response.status_code, 302)

    def test_painel_sem_safra_retorna_200(self):
        response = self.client.get(reverse("posicao:painel"))
        self.assertEqual(response.status_code, 200)

    def test_painel_com_safra_retorna_200(self):
        self._cria_safra()
        response = self.client.get(reverse("posicao:painel"))
        self.assertEqual(response.status_code, 200)

    def test_painel_contexto_tem_posicao(self):
        self._cria_safra()
        response = self.client.get(reverse("posicao:painel"))
        self.assertIn("items", response.context)
        self.assertIn("posicao", response.context["items"][0])

    def test_painel_contexto_tem_safra(self):
        safra = self._cria_safra()
        response = self.client.get(reverse("posicao:painel"))
        self.assertEqual(response.context["items"][0]["safra"], safra)

    def test_painel_nao_mostra_safra_de_outro_produtor(self):
        outro = Produtor.objects.create_user(username="outro", email="outro@test.com")
        Safra.objects.create(
            produtor=outro, cultura="milho", ano_safra="2025/26",
            producao_estimada_sacas=Decimal("500"), custo_por_saca=Decimal("60"),
        )
        response = self.client.get(reverse("posicao:painel"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["items"]), 0)
```

**Substituir** `PainelRiscoViewTestCase` inteira (linhas 237–266) por:

```python
class PainelRiscoViewTestCase(TestCase):
    def setUp(self):
        self.produtor = Produtor.objects.create_user(
            username="risco_view", email="riscoview@test.com", password="senha123"
        )
        Safra.objects.create(
            produtor=self.produtor, cultura="soja", ano_safra="2025/26",
            producao_estimada_sacas=Decimal("1000"), custo_por_saca=Decimal("80"),
        )
        self.client.force_login(self.produtor)
        self.patcher = patch(
            "apps.posicao.views.get_cotacao_com_variacao",
            return_value={
                "cotacao": Decimal("130.00"), "variacao_pct": Decimal("0"),
                "variacao_abs": Decimal("0"), "cambio": Decimal("5.80"), "fonte": "CME/B3",
            },
        )
        self.patcher2 = patch("apps.posicao.views.get_historico_cotacao", return_value=[])
        self.patcher.start()
        self.patcher2.start()

    def tearDown(self):
        self.patcher.stop()
        self.patcher2.stop()

    def test_painel_contexto_tem_risco(self):
        response = self.client.get(reverse("posicao:painel"))
        self.assertIn("items", response.context)
        self.assertIn("risco", response.context["items"][0])

    def test_painel_risco_e_instancia_de_risco_safra(self):
        from apps.posicao.services import RiscoSafra
        response = self.client.get(reverse("posicao:painel"))
        self.assertIsInstance(response.context["items"][0]["risco"], RiscoSafra)
```

**Adicionar** ao final de `apps/posicao/tests.py` — novos testes multi-safra:

```python
class PainelMultiSafraTestCase(TestCase):
    def setUp(self):
        self.produtor = Produtor.objects.create_user(
            username="multi_user", email="multi@test.com", password="senha123"
        )
        self.client.force_login(self.produtor)
        self.patcher = patch(
            "apps.posicao.views.get_cotacao_com_variacao",
            return_value={
                "cotacao": Decimal("130.00"), "variacao_pct": Decimal("0"),
                "variacao_abs": Decimal("0"), "cambio": Decimal("5.80"), "fonte": "CME/B3",
            },
        )
        self.patcher2 = patch("apps.posicao.views.get_historico_cotacao", return_value=[])
        self.patcher.start()
        self.patcher2.start()

    def tearDown(self):
        self.patcher.stop()
        self.patcher2.stop()

    def _cria_safra(self, cultura, ano, ativa=True):
        return Safra.objects.create(
            produtor=self.produtor, cultura=cultura, ano_safra=ano,
            producao_estimada_sacas=Decimal("1000"), custo_por_saca=Decimal("80"), ativa=ativa,
        )

    def test_painel_exibe_todas_safras_ativas(self):
        self._cria_safra("soja", "2025/26")
        self._cria_safra("milho", "2025/26")
        response = self.client.get(reverse("posicao:painel"))
        self.assertEqual(len(response.context["items"]), 2)

    def test_painel_consolida_receita_e_exposicao(self):
        self._cria_safra("soja", "2025/26")
        self._cria_safra("milho", "2025/26")
        response = self.client.get(reverse("posicao:painel"))
        # receita_total = 0 (sem vendas), exposicao_total = 2000 sc × R$130
        self.assertEqual(response.context["receita_total"], Decimal("0"))
        self.assertEqual(response.context["exposicao_total"], Decimal("260000.00"))

    def test_painel_sem_safras_exibe_cta(self):
        response = self.client.get(reverse("posicao:painel"))
        self.assertTrue(response.context["sem_safras"])

    def test_painel_safras_inativas_em_secao_separada(self):
        self._cria_safra("soja", "2025/26", ativa=True)
        self._cria_safra("milho", "2024/25", ativa=False)
        response = self.client.get(reverse("posicao:painel"))
        self.assertEqual(len(response.context["items"]), 1)
        self.assertEqual(response.context["safras_inativas"].count(), 1)
```

- [ ] **Step 2: Rodar testes para confirmar que os antigos quebram e os novos também**

```bash
python manage.py test apps.posicao.tests.PainelViewTestCase apps.posicao.tests.PainelRiscoViewTestCase apps.posicao.tests.PainelMultiSafraTestCase -v 2
```

Esperado: múltiplos FAIL (contexto `items` não existe ainda)

- [ ] **Step 3: Reescrever `apps/posicao/views.py`**

```python
import json
from decimal import Decimal
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from apps.safra.models import Safra
from .services import calcular_posicao, calcular_risco, get_cotacao_atual, get_cotacao_com_variacao, get_historico_cotacao


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
        base = None
        if safra.preco_referencia_local:
            base = (safra.preco_referencia_local - cotacao).quantize(Decimal("0.01"))
        insumos_cobertos = None
        if safra.total_insumos_brl:
            insumos_cobertos = posicao.receita_travada >= safra.total_insumos_brl
        items.append({
            "safra": safra,
            "posicao": posicao,
            "risco": risco,
            "base": base,
            "insumos_cobertos": insumos_cobertos,
        })

    receita_total = sum((i["posicao"].receita_travada for i in items), Decimal("0"))
    exposicao_total = sum(
        (i["posicao"].sacas_a_vender * cotacao for i in items), Decimal("0")
    ).quantize(Decimal("0.01"))
    custo_total = sum((i["posicao"].custo_total for i in items), Decimal("0"))

    return render(request, "posicao/painel.html", {
        "mercado": mercado,
        "cotacao": cotacao,
        "historico_json": json.dumps(historico),
        "items": items,
        "safras_inativas": safras_inativas,
        "receita_total": receita_total,
        "exposicao_total": exposicao_total,
        "custo_total": custo_total,
        "sem_safras": not items and not safras_inativas.exists(),
    })


@login_required
def pdf(request):
    safra = Safra.objects.filter(produtor=request.user, ativa=True).first()
    if not safra:
        return redirect("safra:nova")
    posicao = calcular_posicao(safra)
    cotacao = get_cotacao_atual()
    html = render_to_string("posicao/posicao_pdf.html", {
        "posicao": posicao,
        "safra": safra,
        "cotacao": cotacao,
    })
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="posicao_{safra.id}.pdf"'
    from xhtml2pdf import pisa
    status = pisa.CreatePDF(html, dest=response)
    if status.err:
        return HttpResponse("Erro ao gerar PDF", status=500)
    return response
```

- [ ] **Step 4: Reescrever `templates/posicao/painel.html`**

```html
{% extends "base.html" %}
{% block conteudo %}

<!-- Mercado de Soja -->
<div class="bg-white rounded-2xl p-5 mb-5 shadow-sm border border-slate-100">
  <div class="flex justify-between items-center mb-1">
    <h2 class="font-display font-bold text-green-800 text-lg">Mercado de Soja</h2>
    <span class="text-xs text-slate-400 bg-slate-100 px-2 py-0.5 rounded-full">{{ mercado.fonte }}</span>
  </div>
  <div class="flex items-baseline gap-3 mb-4">
    <span class="font-display text-4xl font-bold text-slate-900">R$ {{ mercado.cotacao }}</span>
    {% if mercado.variacao_pct > 0 %}
    <span class="text-sm font-semibold text-green-600 bg-green-50 px-2 py-0.5 rounded-full">▲ +{{ mercado.variacao_pct }}% (R$ +{{ mercado.variacao_abs }})</span>
    {% elif mercado.variacao_pct < 0 %}
    <span class="text-sm font-semibold text-red-600 bg-red-50 px-2 py-0.5 rounded-full">▼ {{ mercado.variacao_pct }}% (R$ {{ mercado.variacao_abs }})</span>
    {% else %}
    <span class="text-sm text-slate-400">— estável</span>
    {% endif %}
  </div>
  <div style="height:160px">
    <canvas id="chartCotacao"></canvas>
  </div>
</div>
<script>
(function() {
  const dados = JSON.parse('{{ historico_json|escapejs }}');
  const ctx = document.getElementById('chartCotacao');
  if (!ctx || !dados.length) return;
  new Chart(ctx, {
    type: 'line',
    data: {
      labels: dados.map(d => d.data),
      datasets: [{ data: dados.map(d => d.preco), borderColor: 'rgb(22,163,74)', borderWidth: 2, pointRadius: 0, tension: 0.3, fill: false }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { display: false }, ticks: { font: { size: 10 } } },
        y: { grid: { color: 'rgba(0,0,0,0.05)' }, ticks: { font: { size: 10 }, callback: v => 'R$' + v } }
      }
    }
  });
})();
</script>

{% if items|length >= 2 %}
<!-- Consolidado -->
<div class="bg-green-50 border border-green-200 rounded-xl p-4 mb-5">
  <p class="text-xs font-semibold text-green-700 uppercase tracking-wide mb-2">Posição consolidada — {{ items|length }} safras ativas</p>
  <div class="grid grid-cols-3 gap-3 text-center">
    <div>
      <p class="text-xs text-green-600">Receita travada</p>
      <p class="font-bold text-green-900">R$ {{ receita_total }}</p>
    </div>
    <div>
      <p class="text-xs text-green-600">Custo total</p>
      <p class="font-bold text-green-900">R$ {{ custo_total }}</p>
    </div>
    <div>
      <p class="text-xs text-green-600">Exposição aberta</p>
      <p class="font-bold text-amber-700">R$ {{ exposicao_total }}</p>
    </div>
  </div>
</div>
{% endif %}

{% for item in items %}
{% with safra=item.safra posicao=item.posicao risco=item.risco %}
<div class="bg-white rounded-2xl p-5 mb-4 shadow-sm border {% if risco.em_zona_critica %}border-red-300{% else %}border-slate-100{% endif %}">

  <!-- Cabeçalho -->
  <div class="flex justify-between items-center mb-3">
    <div>
      <span class="font-display font-bold text-green-800 text-base">{{ safra.get_cultura_display }} {{ safra.ano_safra }}</span>
      {% if risco.em_zona_critica %}
      <span class="ml-2 text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded-full">zona de risco</span>
      {% endif %}
    </div>
    <span class="text-xs text-slate-400">{{ posicao.sacas_totais }} sc</span>
  </div>

  <!-- Progresso -->
  <div class="mb-3">
    <div class="flex justify-between text-xs text-slate-500 mb-1">
      <span>{{ posicao.percentual_vendido }}% vendido</span>
      <span>{{ posicao.sacas_a_vender }} sc expostas</span>
    </div>
    <div class="w-full bg-slate-200 rounded-full h-2">
      <div class="bg-green-600 h-2 rounded-full" style="width: {{ posicao.percentual_vendido }}%"></div>
    </div>
  </div>

  <!-- Métricas -->
  <div class="grid grid-cols-3 gap-2 mb-3 text-center">
    <div class="bg-slate-50 rounded-lg p-2">
      <p class="text-xs text-slate-500">Receita travada</p>
      <p class="font-bold text-green-700 text-sm">R$ {{ posicao.receita_travada }}</p>
    </div>
    <div class="bg-slate-50 rounded-lg p-2">
      <p class="text-xs text-slate-500">Preço médio</p>
      <p class="font-bold text-slate-800 text-sm">R$ {{ posicao.preco_medio_ponderado }}</p>
    </div>
    <div class="bg-slate-50 rounded-lg p-2">
      <p class="text-xs text-slate-500">Margem</p>
      <p class="font-bold text-sm {% if risco.margem_seguranca >= 0 %}text-green-700{% else %}text-red-600{% endif %}">
        {% if risco.margem_seguranca >= 0 %}+{% endif %}R$ {{ risco.margem_seguranca }}
      </p>
    </div>
  </div>

  <!-- Base local e insumos (quando preenchidos) -->
  {% if item.base is not None or item.insumos_cobertos is not None %}
  <div class="flex gap-3 mb-3 flex-wrap">
    {% if item.base is not None %}
    <span class="text-xs px-2 py-1 rounded-full {% if item.base >= 0 %}bg-green-100 text-green-700{% else %}bg-amber-100 text-amber-700{% endif %}">
      Base local: {% if item.base >= 0 %}+{% endif %}R$ {{ item.base }}/sc
    </span>
    {% endif %}
    {% if item.insumos_cobertos is not None %}
    <span class="text-xs px-2 py-1 rounded-full {% if item.insumos_cobertos %}bg-green-100 text-green-700{% else %}bg-red-100 text-red-700{% endif %}">
      Insumos {% if item.insumos_cobertos %}cobertos ✓{% else %}descobertos ✗{% endif %}
    </span>
    {% endif %}
  </div>
  {% endif %}

  <!-- Botões de ação -->
  <div class="grid grid-cols-2 gap-2">
    <a href="{% url 'vendas:lista' safra.id %}"
       class="text-center text-sm bg-green-700 text-white rounded-xl py-2.5 font-semibold">
      Ver vendas
    </a>
    <a href="{% url 'hedge:cenarios' safra.id %}"
       class="text-center text-sm border border-green-700 text-green-700 rounded-xl py-2.5 font-semibold">
      Cenários
    </a>
    <a href="{% url 'hedge:opcoes' safra.id %}"
       class="text-center text-sm border border-slate-300 text-slate-600 rounded-xl py-2.5 text-xs">
      Opções CME
    </a>
    <a href="{% url 'hedge:cpr' safra.id %}"
       class="text-center text-sm border border-slate-300 text-slate-600 rounded-xl py-2.5 text-xs">
      Simular CPR
    </a>
  </div>
</div>
{% endwith %}
{% endfor %}

{% if safras_inativas.exists %}
<details class="mb-4">
  <summary class="text-sm text-slate-500 cursor-pointer py-2">Safras anteriores ({{ safras_inativas.count }})</summary>
  <div class="mt-2 space-y-2">
    {% for safra in safras_inativas %}
    <div class="bg-slate-50 rounded-xl px-4 py-3 flex justify-between items-center">
      <span class="text-sm text-slate-600">{{ safra.get_cultura_display }} {{ safra.ano_safra }}</span>
      <form method="post" action="{% url 'safra:ativar' safra.id %}">
        {% csrf_token %}
        <button type="submit" class="text-xs text-green-600 underline">Ativar</button>
      </form>
    </div>
    {% endfor %}
  </div>
</details>
{% endif %}

{% if sem_safras %}
<div class="border-2 border-dashed border-green-200 rounded-2xl p-8 text-center">
  <div class="text-4xl mb-3">🌱</div>
  <h3 class="font-display text-lg font-bold text-green-800 mb-2">Cadastre sua safra</h3>
  <p class="text-slate-500 text-sm mb-5">Veja sua posição de hedge, preço médio e risco em tempo real.</p>
  <a href="{% url 'safra:nova' %}"
     class="inline-block bg-green-700 hover:bg-green-800 text-white rounded-xl px-6 py-3 font-semibold transition-colors">
    Cadastrar safra
  </a>
</div>
{% endif %}

{% endblock %}
```

- [ ] **Step 5: Rodar testes**

```bash
python manage.py test apps.posicao.tests.PainelViewTestCase apps.posicao.tests.PainelRiscoViewTestCase apps.posicao.tests.PainelMultiSafraTestCase -v 2
```

Esperado: todos PASS

- [ ] **Step 6: Rodar suite completa**

```bash
python manage.py test
```

Esperado: 171 testes OK (167 + 4 novos, 5 atualizados)

- [ ] **Step 7: Commit**

```bash
git add apps/posicao/views.py apps/posicao/tests.py templates/posicao/painel.html
git commit -m "feat: dashboard multi-safra com consolidado, base local e insumos"
```

---

## Task 4: Simulador CPR

**Files:**
- Modify: `apps/hedge/urls.py`
- Modify: `apps/hedge/views.py`
- Modify: `apps/hedge/tests.py`
- Create: `templates/hedge/cpr.html`
- Modify: `templates/hedge/estrategias.html`

- [ ] **Step 1: Adicionar URL**

Em `apps/hedge/urls.py`, adicionar após a rota `opcoes`:

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
    path("<int:safra_id>/cpr/", views.simulador_cpr, name="cpr"),
]
```

- [ ] **Step 2: Escrever testes**

Adicionar ao final de `apps/hedge/tests.py`:

```python
class SimuladorCprTestCase(TestCase):
    def setUp(self):
        self.produtor = Produtor.objects.create_user(
            username="cpr_user", email="cpr@test.com", password="senha123"
        )
        self.safra = Safra.objects.create(
            produtor=self.produtor, cultura="soja", ano_safra="2025/26",
            producao_estimada_sacas=Decimal("1000"), custo_por_saca=Decimal("80"),
        )
        self.client.force_login(self.produtor)

    def test_cpr_retorna_200(self):
        with patch("apps.hedge.views.get_cotacao_atual", return_value=Decimal("130.00")):
            response = self.client.get(reverse("hedge:cpr", args=[self.safra.id]))
        self.assertEqual(response.status_code, 200)

    def test_cpr_requer_login(self):
        self.client.logout()
        response = self.client.get(reverse("hedge:cpr", args=[self.safra.id]))
        self.assertEqual(response.status_code, 302)

    def test_cpr_passa_cotacao_e_cdi_para_template(self):
        with patch("apps.hedge.views.get_cotacao_atual", return_value=Decimal("130.00")):
            response = self.client.get(reverse("hedge:cpr", args=[self.safra.id]))
        self.assertIn("cotacao_atual", response.context)
        self.assertIn("cdi_anual", response.context)
        self.assertAlmostEqual(response.context["cotacao_atual"], 130.0)
        self.assertAlmostEqual(response.context["cdi_anual"], 14.75)
```

- [ ] **Step 3: Rodar testes para confirmar falha**

```bash
python manage.py test apps.hedge.tests.SimuladorCprTestCase -v 2
```

Esperado: FAIL — `AttributeError: module 'apps.hedge.views' has no attribute 'simulador_cpr'`

- [ ] **Step 4: Adicionar view `simulador_cpr` em `apps/hedge/views.py`**

Adicionar ao final do arquivo (após a view `opcoes`):

```python
@login_required
def simulador_cpr(request, safra_id):
    safra = get_object_or_404(Safra, id=safra_id, produtor=request.user)
    cotacao = get_cotacao_atual()
    return render(request, "hedge/cpr.html", {
        "safra": safra,
        "cotacao_atual": float(cotacao),
        "cdi_anual": 14.75,
    })
```

- [ ] **Step 5: Criar `templates/hedge/cpr.html`**

```html
{% extends "base.html" %}
{% block conteudo %}

<div class="mb-4">
  <a href="{% url 'posicao:painel' %}" class="text-sm text-green-600">← Voltar ao painel</a>
  <h1 class="font-display text-2xl font-bold text-green-800 mt-2">Simulador CPR</h1>
  <p class="text-sm text-slate-500 mt-1">{{ safra.get_cultura_display }} {{ safra.ano_safra }}</p>
</div>

<div class="bg-white rounded-2xl p-5 mb-5 shadow-sm border border-slate-100">
  <h2 class="font-semibold text-slate-700 mb-4">Parâmetros</h2>

  <div class="space-y-4">
    <div>
      <label class="block text-sm font-medium text-slate-700 mb-1.5">Cotação spot hoje (R$/sc)</label>
      <input type="number" id="spotInput" step="0.01" min="0"
             value="{{ cotacao_atual }}"
             class="w-full border border-slate-300 rounded-xl px-3 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
             oninput="calcular()">
    </div>
    <div>
      <label class="block text-sm font-medium text-slate-700 mb-1.5">Preço CPR ofertado (R$/sc)</label>
      <input type="number" id="cprInput" step="0.01" min="0"
             value="{{ cotacao_atual }}"
             class="w-full border border-slate-300 rounded-xl px-3 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
             oninput="calcular()">
    </div>
    <div class="grid grid-cols-2 gap-4">
      <div>
        <label class="block text-sm font-medium text-slate-700 mb-1.5">Prazo (dias)</label>
        <input type="number" id="prazoInput" step="1" min="1" value="180"
               class="w-full border border-slate-300 rounded-xl px-3 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
               oninput="calcular()">
      </div>
      <div>
        <label class="block text-sm font-medium text-slate-700 mb-1.5">CDI referência (% a.a.)</label>
        <input type="number" id="cdiInput" step="0.01" min="0"
               value="{{ cdi_anual }}"
               class="w-full border border-slate-300 rounded-xl px-3 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
               oninput="calcular()">
      </div>
    </div>
  </div>
</div>

<div class="bg-white rounded-2xl p-5 mb-5 shadow-sm border border-slate-100" id="resultado">
  <h2 class="font-semibold text-slate-700 mb-4">Resultado</h2>

  <div class="grid grid-cols-2 gap-3 mb-4">
    <div class="bg-green-50 rounded-xl p-3 text-center">
      <p class="text-xs text-green-700">Taxa efetiva da CPR</p>
      <p class="font-display text-2xl font-bold text-green-800" id="taxaCpr">—</p>
      <p class="text-xs text-green-600">% ao ano</p>
    </div>
    <div class="bg-slate-50 rounded-xl p-3 text-center">
      <p class="text-xs text-slate-600">Para ganhar mais que o CDI</p>
      <p class="font-display text-2xl font-bold text-slate-800" id="breakeven">—</p>
      <p class="text-xs text-slate-500">R$/sc no vencimento</p>
    </div>
  </div>

  <div class="rounded-xl p-4 mb-4" id="veredictoBox">
    <p class="text-sm font-semibold" id="veredictoTexto">—</p>
  </div>

  <h3 class="text-sm font-semibold text-slate-700 mb-2">Comparativo por cenário de preço</h3>
  <div class="overflow-x-auto">
    <table class="w-full text-sm">
      <thead>
        <tr class="text-xs text-slate-500 border-b">
          <th class="text-left py-2">Alta do spot</th>
          <th class="text-right py-2">Spot no vencimento</th>
          <th class="text-right py-2">CPR vale mais?</th>
        </tr>
      </thead>
      <tbody id="tabelaBreakeven"></tbody>
    </table>
  </div>
</div>

<div class="bg-amber-50 border border-amber-200 rounded-xl p-4 text-sm text-amber-800">
  <p class="font-semibold mb-1">Como interpretar</p>
  <p>A CPR trava o preço agora. Se o mercado subir acima do breakeven, você teria ganho mais esperando. Se cair, a CPR te protege.</p>
</div>

<script>
const VARIACOES = [0, 5, 10, 15, 20];

function calcular() {
  const spot = parseFloat(document.getElementById('spotInput').value) || 0;
  const cpr = parseFloat(document.getElementById('cprInput').value) || 0;
  const prazo = parseFloat(document.getElementById('prazoInput').value) || 1;
  const cdi = parseFloat(document.getElementById('cdiInput').value) || 0;

  if (spot <= 0 || cpr <= 0) return;

  // Taxa efetiva da CPR
  const taxaEfetiva = (Math.pow(cpr / spot, 365 / prazo) - 1) * 100;

  // Spot equivalente no vencimento para superar a CPR
  const breakevenSpot = spot * Math.pow(1 + cdi / 100, prazo / 365);

  document.getElementById('taxaCpr').textContent = taxaEfetiva.toFixed(2) + '%';
  document.getElementById('breakeven').textContent = 'R$ ' + breakevenSpot.toFixed(2);

  const cprVale = taxaEfetiva >= cdi;
  const box = document.getElementById('veredictoBox');
  const txt = document.getElementById('veredictoTexto');
  if (cprVale) {
    box.className = 'rounded-xl p-4 mb-4 bg-green-50 border border-green-200';
    txt.className = 'text-sm font-semibold text-green-800';
    txt.textContent = 'CPR vale mais que esperar — taxa de ' + taxaEfetiva.toFixed(2) + '% a.a. supera o CDI de ' + cdi + '% a.a.';
  } else {
    box.className = 'rounded-xl p-4 mb-4 bg-amber-50 border border-amber-200';
    txt.className = 'text-sm font-semibold text-amber-800';
    txt.textContent = 'Esperando no mercado rende mais se o preço subir acima de R$ ' + breakevenSpot.toFixed(2) + '/sc.';
  }

  // Tabela
  const tbody = document.getElementById('tabelaBreakeven');
  tbody.innerHTML = '';
  VARIACOES.forEach(pct => {
    const spotVenc = spot * (1 + pct / 100);
    const cprGanha = cpr >= spotVenc;
    const tr = document.createElement('tr');
    tr.className = 'border-b border-slate-100';
    tr.innerHTML = `
      <td class="py-2 text-slate-600">+${pct}%</td>
      <td class="py-2 text-right font-semibold">R$ ${spotVenc.toFixed(2)}</td>
      <td class="py-2 text-right">
        <span class="px-2 py-0.5 rounded-full text-xs font-semibold ${cprGanha ? 'bg-green-100 text-green-700' : 'bg-slate-100 text-slate-500'}">
          ${cprGanha ? 'Sim' : 'Não'}
        </span>
      </td>`;
    tbody.appendChild(tr);
  });
}

document.addEventListener('DOMContentLoaded', calcular);
</script>

{% endblock %}
```

- [ ] **Step 6: Adicionar link CPR em `templates/hedge/estrategias.html`**

Antes do `{% endblock %}` final de `templates/hedge/estrategias.html`, adicionar:

```html
<a href="{% url 'hedge:cpr' safra.id %}"
   class="block w-full border border-slate-300 text-slate-600 text-center rounded-xl py-3 font-semibold mt-3 min-h-[48px] text-sm">
  Simular CPR vs venda spot →
</a>
```

- [ ] **Step 7: Rodar testes**

```bash
python manage.py test apps.hedge.tests.SimuladorCprTestCase -v 2
```

Esperado: 3 testes PASS

- [ ] **Step 8: Rodar suite completa**

```bash
python manage.py test
```

Esperado: 174 testes OK

- [ ] **Step 9: Commit**

```bash
git add apps/hedge/urls.py apps/hedge/views.py apps/hedge/tests.py templates/hedge/cpr.html templates/hedge/estrategias.html
git commit -m "feat: simulador CPR vs venda spot"
```
