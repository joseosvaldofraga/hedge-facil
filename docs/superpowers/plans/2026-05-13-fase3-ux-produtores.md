# HedgeFácil Fase 3 — UX Produtores

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Editar e deletar vendas + navegação entre múltiplas safras com troca de safra ativa.

**Architecture:** Mesmos padrões da Fase 1/2 — Django views com HTMX para atualizações parciais. Venda edit/delete retornam `_lista.html` fragment em HTMX requests. Safra ativar usa transação atômica para garantir exatamente uma safra ativa por produtor.

**Tech Stack:** Django 6, HTMX 2.0, `@login_required`, `@require_POST`, `get_object_or_404`, `django.db.transaction.atomic`.

---

## Arquivos modificados/criados

| Arquivo | Ação |
|---------|------|
| `apps/vendas/views.py` | Adiciona `editar`, `deletar` |
| `apps/vendas/urls.py` | Adiciona `<id>/editar/`, `<id>/deletar/` |
| `apps/vendas/tests.py` | Adiciona 10 testes |
| `templates/vendas/_lista.html` | Adiciona botões editar e deletar |
| `apps/safra/views.py` | Adiciona `lista`, `ativar` |
| `apps/safra/urls.py` | Adiciona `""` (lista) e `<id>/ativar/` |
| `apps/safra/tests.py` | Adiciona 7 testes |
| `templates/safra/lista.html` | Cria novo template |
| `templates/posicao/painel.html` | Adiciona link "Trocar safra" |

---

## Task 1: Editar Venda (TDD)

**Files:**
- Modify: `apps/vendas/views.py`
- Modify: `apps/vendas/urls.py`
- Modify: `apps/vendas/tests.py`
- Modify: `templates/vendas/_lista.html`

- [ ] **Step 1: Write failing tests**

Add to `apps/vendas/tests.py` — new class after the existing classes. Read the file first to find the last line and check existing imports (need `Venda`).

```python
class VendaEditarTestCase(TestCase):
    def setUp(self):
        self.produtor = Produtor.objects.create_user(
            username="edit_user", email="edit@test.com", password="senha123"
        )
        self.safra = Safra.objects.create(
            produtor=self.produtor,
            cultura="soja",
            ano_safra="2025/26",
            producao_estimada_sacas=Decimal("1000"),
            custo_por_saca=Decimal("80"),
        )
        self.venda = Venda.objects.create(
            safra=self.safra,
            tipo="balcao",
            contraparte="Cargill",
            sacas=Decimal("300"),
            preco_por_saca=Decimal("120"),
            data_negociacao="2025-03-01",
        )
        self.client.force_login(self.produtor)

    def test_editar_requer_login(self):
        self.client.logout()
        url = reverse("vendas:editar", args=[self.venda.id])
        self.assertEqual(self.client.get(url).status_code, 302)

    def test_editar_get_retorna_200(self):
        url = reverse("vendas:editar", args=[self.venda.id])
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_editar_get_404_para_venda_de_outro_produtor(self):
        outro = Produtor.objects.create_user(
            username="outro_edit", email="outro_edit@test.com", password="senha123"
        )
        self.client.force_login(outro)
        url = reverse("vendas:editar", args=[self.venda.id])
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_editar_post_valido_atualiza_venda(self):
        url = reverse("vendas:editar", args=[self.venda.id])
        self.client.post(url, {
            "tipo": "balcao",
            "contraparte": "Bunge",
            "sacas": "300",
            "preco_por_saca": "130.00",
            "data_negociacao": "2025-03-01",
        })
        self.venda.refresh_from_db()
        self.assertEqual(self.venda.contraparte, "Bunge")
        self.assertEqual(self.venda.preco_por_saca, Decimal("130.00"))

    def test_editar_post_valido_redireciona_para_lista(self):
        url = reverse("vendas:editar", args=[self.venda.id])
        response = self.client.post(url, {
            "tipo": "balcao",
            "contraparte": "Bunge",
            "sacas": "300",
            "preco_por_saca": "130.00",
            "data_negociacao": "2025-03-01",
        })
        self.assertRedirects(
            response,
            reverse("vendas:lista", args=[self.safra.id]),
            fetch_redirect_response=False,
        )

    def test_editar_post_invalido_retorna_200_com_erros(self):
        url = reverse("vendas:editar", args=[self.venda.id])
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors)
```

- [ ] **Step 2: Run RED**

```bash
cd /media/fragatec/SSD/projetos/web/hedgefacil
.venv/bin/python manage.py test apps.vendas.tests.VendaEditarTestCase
```

Expected: `NoReverseMatch` for `vendas:editar` → RED ✓

- [ ] **Step 3: Add URL**

Edit `apps/vendas/urls.py`, add before the closing `]`:

```python
from django.urls import path
from . import views

app_name = "vendas"

urlpatterns = [
    path("<int:safra_id>/", views.lista, name="lista"),
    path("nova/<int:safra_id>/", views.nova, name="nova"),
    path("<int:venda_id>/editar/", views.editar, name="editar"),
]
```

- [ ] **Step 4: Implement editar view**

Add to `apps/vendas/views.py` (after `nova`):

```python
@login_required
def editar(request, venda_id):
    venda = get_object_or_404(Venda, id=venda_id, safra__produtor=request.user)
    safra = venda.safra
    if request.method == "POST":
        form = VendaForm(request.POST, instance=venda)
        if form.is_valid():
            form.save()
            if request.htmx:
                return render(request, "vendas/_lista.html", {
                    "vendas": safra.vendas.all(), "safra": safra,
                })
            return redirect("vendas:lista", safra_id=safra.id)
    else:
        form = VendaForm(instance=venda)
    return render(request, "vendas/_form.html", {"form": form, "safra": safra})
```

- [ ] **Step 5: Run GREEN**

```bash
.venv/bin/python manage.py test apps.vendas.tests.VendaEditarTestCase
```

Expected: 6 PASS ✓

- [ ] **Step 6: Add edit button to `_lista.html`**

Read `templates/vendas/_lista.html`, then add editar button inside each item div, after the existing content:

```html
{% for venda in vendas %}
<div class="bg-white rounded-lg p-4 mb-3 shadow-sm border border-slate-100">
  <div class="flex justify-between">
    <span class="font-semibold">{{ venda.contraparte }}</span>
    <span class="text-green-700 font-bold">R$ {{ venda.preco_por_saca }}</span>
  </div>
  <div class="text-sm text-slate-500 mt-1">
    {{ venda.sacas }} sc · {{ venda.get_tipo_display }} · {{ venda.data_negociacao }}
  </div>
  <div class="flex gap-2 mt-2">
    <button hx-get="{% url 'vendas:editar' venda.id %}"
            hx-target="#venda-form-container"
            hx-swap="innerHTML"
            class="text-xs text-blue-600 border border-blue-300 rounded px-2 py-1">
      Editar
    </button>
  </div>
</div>
{% empty %}
<p class="text-slate-500 text-center py-8">Nenhuma venda lançada ainda.</p>
{% endfor %}
```

- [ ] **Step 7: Run all tests**

```bash
.venv/bin/python manage.py test
```

Expected: 95 tests (89 + 6), all OK.

- [ ] **Step 8: Commit**

```bash
git add apps/vendas/views.py apps/vendas/urls.py apps/vendas/tests.py templates/vendas/_lista.html
git commit -m "$(cat <<'EOF'
task 1: editar venda com TDD, botão editar inline via HTMX

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Deletar Venda (TDD)

**Files:**
- Modify: `apps/vendas/views.py`
- Modify: `apps/vendas/urls.py`
- Modify: `apps/vendas/tests.py`
- Modify: `templates/vendas/_lista.html`

- [ ] **Step 1: Write failing tests**

Add to `apps/vendas/tests.py`, after `VendaEditarTestCase`:

```python
class VendaDeletarTestCase(TestCase):
    def setUp(self):
        self.produtor = Produtor.objects.create_user(
            username="del_user", email="del@test.com", password="senha123"
        )
        self.safra = Safra.objects.create(
            produtor=self.produtor,
            cultura="soja",
            ano_safra="2025/26",
            producao_estimada_sacas=Decimal("1000"),
            custo_por_saca=Decimal("80"),
        )
        self.venda = Venda.objects.create(
            safra=self.safra,
            tipo="balcao",
            contraparte="Cargill",
            sacas=Decimal("300"),
            preco_por_saca=Decimal("120"),
            data_negociacao="2025-03-01",
        )
        self.client.force_login(self.produtor)

    def test_deletar_requer_login(self):
        self.client.logout()
        url = reverse("vendas:deletar", args=[self.venda.id])
        self.assertEqual(self.client.post(url).status_code, 302)

    def test_deletar_post_remove_venda(self):
        url = reverse("vendas:deletar", args=[self.venda.id])
        self.client.post(url)
        self.assertEqual(Venda.objects.count(), 0)

    def test_deletar_post_404_para_venda_de_outro_produtor(self):
        outro = Produtor.objects.create_user(
            username="outro_del", email="outro_del@test.com", password="senha123"
        )
        self.client.force_login(outro)
        url = reverse("vendas:deletar", args=[self.venda.id])
        self.assertEqual(self.client.post(url).status_code, 404)

    def test_deletar_get_nao_permitido(self):
        url = reverse("vendas:deletar", args=[self.venda.id])
        self.assertEqual(self.client.get(url).status_code, 405)
```

- [ ] **Step 2: Run RED**

```bash
.venv/bin/python manage.py test apps.vendas.tests.VendaDeletarTestCase
```

Expected: `NoReverseMatch` for `vendas:deletar` → RED ✓

- [ ] **Step 3: Add URL**

Edit `apps/vendas/urls.py`:

```python
from django.urls import path
from . import views

app_name = "vendas"

urlpatterns = [
    path("<int:safra_id>/", views.lista, name="lista"),
    path("nova/<int:safra_id>/", views.nova, name="nova"),
    path("<int:venda_id>/editar/", views.editar, name="editar"),
    path("<int:venda_id>/deletar/", views.deletar, name="deletar"),
]
```

- [ ] **Step 4: Implement deletar view**

Add to `apps/vendas/views.py`. Import `require_POST` at top:

```python
from django.views.decorators.http import require_POST
```

Then add the view:

```python
@login_required
@require_POST
def deletar(request, venda_id):
    venda = get_object_or_404(Venda, id=venda_id, safra__produtor=request.user)
    safra = venda.safra
    venda.delete()
    if request.htmx:
        return render(request, "vendas/_lista.html", {
            "vendas": safra.vendas.all(), "safra": safra,
        })
    return redirect("vendas:lista", safra_id=safra.id)
```

- [ ] **Step 5: Run GREEN**

```bash
.venv/bin/python manage.py test apps.vendas.tests.VendaDeletarTestCase
```

Expected: 4 PASS ✓

- [ ] **Step 6: Add delete button to `_lista.html`**

Read `templates/vendas/_lista.html`. Add deletar button alongside the editar button in the `<div class="flex gap-2 mt-2">` div:

```html
{% for venda in vendas %}
<div class="bg-white rounded-lg p-4 mb-3 shadow-sm border border-slate-100">
  <div class="flex justify-between">
    <span class="font-semibold">{{ venda.contraparte }}</span>
    <span class="text-green-700 font-bold">R$ {{ venda.preco_por_saca }}</span>
  </div>
  <div class="text-sm text-slate-500 mt-1">
    {{ venda.sacas }} sc · {{ venda.get_tipo_display }} · {{ venda.data_negociacao }}
  </div>
  <div class="flex gap-2 mt-2">
    <button hx-get="{% url 'vendas:editar' venda.id %}"
            hx-target="#venda-form-container"
            hx-swap="innerHTML"
            class="text-xs text-blue-600 border border-blue-300 rounded px-2 py-1">
      Editar
    </button>
    <button hx-post="{% url 'vendas:deletar' venda.id %}"
            hx-target="#lista-vendas"
            hx-swap="outerHTML"
            hx-confirm="Deletar esta venda?"
            hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'
            class="text-xs text-red-600 border border-red-300 rounded px-2 py-1">
      Deletar
    </button>
  </div>
</div>
{% empty %}
<p class="text-slate-500 text-center py-8">Nenhuma venda lançada ainda.</p>
{% endfor %}
```

Note: `_lista.html` is a partial and needs CSRF token for the HTMX post. The `hx-headers` with `csrf_token` is the correct way to pass CSRF in a partial that has no `<form>` tag. The outerHTML swap requires `_lista.html` to include the wrapping `<div id="lista-vendas">` — update `_lista.html` to wrap in that div:

```html
<div id="lista-vendas">
{% for venda in vendas %}
...
{% endfor %}
</div>
```

Wait — currently `lista-vendas` wrapper is in `lista.html`, not `_lista.html`. The partial `_lista.html` is the content *inside* `#lista-vendas`. But the deletar button targets `#lista-vendas` with `outerHTML`, which means `_lista.html` needs to include the `<div id="lista-vendas">` wrapper itself.

Update `templates/vendas/_lista.html` to include the wrapper:

```html
<div id="lista-vendas">
  {% for venda in vendas %}
  <div class="bg-white rounded-lg p-4 mb-3 shadow-sm border border-slate-100">
    <div class="flex justify-between">
      <span class="font-semibold">{{ venda.contraparte }}</span>
      <span class="text-green-700 font-bold">R$ {{ venda.preco_por_saca }}</span>
    </div>
    <div class="text-sm text-slate-500 mt-1">
      {{ venda.sacas }} sc · {{ venda.get_tipo_display }} · {{ venda.data_negociacao }}
    </div>
    <div class="flex gap-2 mt-2">
      <button hx-get="{% url 'vendas:editar' venda.id %}"
              hx-target="#venda-form-container"
              hx-swap="innerHTML"
              class="text-xs text-blue-600 border border-blue-300 rounded px-2 py-1">
        Editar
      </button>
      <button hx-post="{% url 'vendas:deletar' venda.id %}"
              hx-target="#lista-vendas"
              hx-swap="outerHTML"
              hx-confirm="Deletar esta venda?"
              hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'
              class="text-xs text-red-600 border border-red-300 rounded px-2 py-1">
        Deletar
      </button>
    </div>
  </div>
  {% empty %}
  <p class="text-slate-500 text-center py-8">Nenhuma venda lançada ainda.</p>
  {% endfor %}
</div>
```

And update `templates/vendas/lista.html` to NOT wrap the include in `<div id="lista-vendas">` (since `_lista.html` now provides the wrapper):

```html
{% extends "base.html" %}
{% block conteudo %}
<div class="flex justify-between items-center mb-4">
  <h1 class="font-display text-xl font-bold text-green-800">Vendas — {{ safra }}</h1>
  <button hx-get="{% url 'vendas:nova' safra.id %}"
          hx-target="#venda-form-container"
          hx-swap="innerHTML"
          class="bg-green-700 text-white px-4 py-2 rounded-lg text-sm font-semibold">
    + Nova
  </button>
</div>
<div id="venda-form-container"></div>
{% include "vendas/_lista.html" %}
{% endblock %}
```

Also check: the nova view on HTMX POST success returns `_lista.html` — this is now correct since it includes the `#lista-vendas` wrapper for outerHTML swap. Verify the existing HTMX nova test still passes.

- [ ] **Step 7: Run all tests**

```bash
.venv/bin/python manage.py test
```

Expected: 99 tests (95 + 4), all OK.

- [ ] **Step 8: Commit**

```bash
git add apps/vendas/views.py apps/vendas/urls.py apps/vendas/tests.py templates/vendas/_lista.html templates/vendas/lista.html
git commit -m "$(cat <<'EOF'
task 2: deletar venda com TDD, botão deletar com confirmação HTMX

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Lista de Safras + Ativar (TDD)

**Files:**
- Modify: `apps/safra/views.py`
- Modify: `apps/safra/urls.py`
- Modify: `apps/safra/tests.py`
- Create: `templates/safra/lista.html`
- Modify: `templates/posicao/painel.html`

- [ ] **Step 1: Write failing tests**

Add to `apps/safra/tests.py`, after `SafraNovaViewTestCase`:

```python
class SafraListaViewTestCase(TestCase):
    def setUp(self):
        self.produtor = Produtor.objects.create_user(
            username="lista_user", email="lista@test.com", password="senha123"
        )
        self.safra1 = Safra.objects.create(
            produtor=self.produtor, cultura="soja", ano_safra="2025/26",
            producao_estimada_sacas=Decimal("1000"), custo_por_saca=Decimal("80"), ativa=True,
        )
        self.safra2 = Safra.objects.create(
            produtor=self.produtor, cultura="milho", ano_safra="2025/26",
            producao_estimada_sacas=Decimal("500"), custo_por_saca=Decimal("60"), ativa=False,
        )
        self.client.force_login(self.produtor)

    def test_lista_requer_login(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse("safra:lista")).status_code, 302)

    def test_lista_retorna_200(self):
        self.assertEqual(self.client.get(reverse("safra:lista")).status_code, 200)

    def test_lista_mostra_safras_do_usuario(self):
        response = self.client.get(reverse("safra:lista"))
        self.assertIn(self.safra1, response.context["safras"])
        self.assertIn(self.safra2, response.context["safras"])

    def test_lista_nao_mostra_safras_de_outros_produtores(self):
        outro = Produtor.objects.create_user(
            username="outro_lista", email="outro_lista@test.com", password="senha123"
        )
        safra_outro = Safra.objects.create(
            produtor=outro, cultura="soja", ano_safra="2025/26",
            producao_estimada_sacas=Decimal("1000"), custo_por_saca=Decimal("80"),
        )
        response = self.client.get(reverse("safra:lista"))
        self.assertNotIn(safra_outro, response.context["safras"])


class SafraAtivarViewTestCase(TestCase):
    def setUp(self):
        self.produtor = Produtor.objects.create_user(
            username="ativar_user", email="ativar@test.com", password="senha123"
        )
        self.safra1 = Safra.objects.create(
            produtor=self.produtor, cultura="soja", ano_safra="2025/26",
            producao_estimada_sacas=Decimal("1000"), custo_por_saca=Decimal("80"), ativa=True,
        )
        self.safra2 = Safra.objects.create(
            produtor=self.produtor, cultura="milho", ano_safra="2025/26",
            producao_estimada_sacas=Decimal("500"), custo_por_saca=Decimal("60"), ativa=False,
        )
        self.client.force_login(self.produtor)

    def test_ativar_requer_login(self):
        self.client.logout()
        url = reverse("safra:ativar", args=[self.safra2.id])
        self.assertEqual(self.client.post(url).status_code, 302)

    def test_ativar_post_muda_safra_ativa(self):
        url = reverse("safra:ativar", args=[self.safra2.id])
        self.client.post(url)
        self.safra1.refresh_from_db()
        self.safra2.refresh_from_db()
        self.assertFalse(self.safra1.ativa)
        self.assertTrue(self.safra2.ativa)

    def test_ativar_redireciona_para_painel(self):
        url = reverse("safra:ativar", args=[self.safra2.id])
        response = self.client.post(url)
        self.assertRedirects(response, reverse("posicao:painel"), fetch_redirect_response=False)
```

- [ ] **Step 2: Run RED**

```bash
.venv/bin/python manage.py test apps.safra.tests.SafraListaViewTestCase apps.safra.tests.SafraAtivarViewTestCase
```

Expected: `NoReverseMatch` for `safra:lista` → RED ✓

- [ ] **Step 3: Add URLs**

Edit `apps/safra/urls.py`:

```python
from django.urls import path
from . import views

app_name = "safra"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("nova/", views.nova, name="nova"),
    path("<int:safra_id>/ativar/", views.ativar, name="ativar"),
]
```

- [ ] **Step 4: Implement lista and ativar views**

Edit `apps/safra/views.py`:

```python
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db import transaction
from .forms import SafraForm
from .models import Safra


@login_required
def lista(request):
    safras = request.user.safras.all()
    return render(request, "safra/lista.html", {"safras": safras})


@login_required
def nova(request):
    if request.method == "POST":
        form = SafraForm(request.POST)
        if form.is_valid():
            safra = form.save(commit=False)
            safra.produtor = request.user
            safra.save()
            return redirect("posicao:painel")
    else:
        form = SafraForm()
    primeiro_acesso = request.user.safras.count() == 0
    return render(request, "safra/nova.html", {
        "form": form,
        "primeiro_acesso": primeiro_acesso,
    })


@login_required
@require_POST
def ativar(request, safra_id):
    safra = get_object_or_404(Safra, id=safra_id, produtor=request.user)
    with transaction.atomic():
        request.user.safras.update(ativa=False)
        safra.ativa = True
        safra.save()
    return redirect("posicao:painel")
```

- [ ] **Step 5: Run GREEN**

```bash
.venv/bin/python manage.py test apps.safra.tests.SafraListaViewTestCase apps.safra.tests.SafraAtivarViewTestCase
```

Expected: 7 PASS ✓

- [ ] **Step 6: Create `templates/safra/lista.html`**

```html
{% extends "base.html" %}
{% block conteudo %}
<div class="flex justify-between items-center mb-6">
  <h1 class="font-display text-2xl font-bold text-green-800">Minhas Safras</h1>
  <a href="{% url 'safra:nova' %}"
     class="bg-green-700 text-white px-4 py-2 rounded-lg text-sm font-semibold">
    + Nova
  </a>
</div>

{% for safra in safras %}
<div class="bg-white rounded-xl p-4 mb-3 shadow-sm border {% if safra.ativa %}border-green-400{% else %}border-slate-100{% endif %}">
  <div class="flex justify-between items-start">
    <div>
      <p class="font-semibold text-slate-800">{{ safra.get_cultura_display }} {{ safra.ano_safra }}</p>
      <p class="text-xs text-slate-500 mt-1">{{ safra.producao_estimada_sacas }} sc · R$ {{ safra.custo_por_saca }}/sc</p>
    </div>
    {% if safra.ativa %}
    <span class="text-xs font-semibold text-green-700 bg-green-50 border border-green-200 rounded-full px-2 py-1">Ativa</span>
    {% else %}
    <form method="post" action="{% url 'safra:ativar' safra.id %}">
      {% csrf_token %}
      <button type="submit"
              class="text-xs text-slate-600 border border-slate-300 rounded-full px-2 py-1">
        Ativar
      </button>
    </form>
    {% endif %}
  </div>
</div>
{% empty %}
<p class="text-slate-500 text-center py-8">Nenhuma safra cadastrada.</p>
{% endfor %}
{% endblock %}
```

- [ ] **Step 7: Add "Trocar safra" link to painel**

Read `templates/posicao/painel.html`. After the `<p class="text-sm text-slate-500">{{ safra }}</p>` line, add a small link:

```html
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
```

- [ ] **Step 8: Run all tests**

```bash
.venv/bin/python manage.py test
```

Expected: 106 tests (99 + 7), all OK.

- [ ] **Step 9: Commit**

```bash
git add apps/safra/views.py apps/safra/urls.py apps/safra/tests.py templates/safra/lista.html templates/posicao/painel.html
git commit -m "$(cat <<'EOF'
task 3: lista de safras, ativar safra, link trocar no painel

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Verificação final

```bash
.venv/bin/python manage.py test
# Expected: 106 tests, all OK

.venv/bin/python manage.py check
# Expected: System check identified no issues
```

## Contagem de testes

| Task | Novos | Total |
|------|-------|-------|
| Baseline | — | 89 |
| Task 1 (editar venda) | 6 | 95 |
| Task 2 (deletar venda) | 4 | 99 |
| Task 3 (lista + ativar) | 7 | 106 |
