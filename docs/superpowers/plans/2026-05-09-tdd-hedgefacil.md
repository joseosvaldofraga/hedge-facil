# HedgeFácil TDD — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementar o HedgeFácil do zero usando TDD — cada feature começa com teste falhando, depois implementação mínima, depois refatoração.

**Architecture:** Mini-sprints TDD seguindo o roadmap do CLAUDE.md. Cada sprint cobre models → services → views, sempre na ordem test → implement → commit. Services financeiros são a prioridade de qualidade — cálculo errado = produtor toma decisão errada.

**Tech Stack:** Django 6 + HTMX + SQLite (dev) + django-sesame + django-htmx + crispy-tailwind

---

## Mapa de Arquivos

### Criar
- `tests/__init__.py` — torna o diretório tests/ descobrível pelo Django test runner
- `tests/test_modelos.py` — testes de Produtor, Safra, Venda (propriedades, constraints)
- `tests/test_calculos.py` — testes de calcular_posicao e simular_cenarios
- `apps/contas/models.py` — Produtor(AbstractUser)
- `apps/contas/views.py` — solicitar_login, email_enviado
- `apps/contas/urls.py` — URLs de auth
- `apps/contas/tests.py` — testes de login mágico
- `apps/safra/models.py` — Safra, Cultura
- `apps/safra/forms.py` — SafraForm
- `apps/safra/views.py` — nova safra
- `apps/safra/urls.py` — URLs de safra
- `apps/vendas/models.py` — Venda, TipoVenda
- `apps/vendas/forms.py` — VendaForm
- `apps/vendas/views.py` — lista, nova (com HTMX)
- `apps/vendas/urls.py` — URLs de vendas
- `apps/vendas/tests.py` — testes de views + HTMX
- `apps/posicao/services.py` — calcular_posicao() → PosicaoSafra
- `apps/posicao/views.py` — painel
- `apps/posicao/urls.py` — URLs de posição
- `apps/posicao/tests.py` — testes de view do painel
- `apps/hedge/services.py` — simular_cenarios() → list[CenarioPreco]
- `apps/hedge/views.py` — cenarios, proteger
- `apps/hedge/urls.py` — URLs de hedge
- `apps/hedge/tests.py` — testes de views de hedge
- `templates/contas/login.html`
- `templates/contas/email_enviado.html`
- `templates/safra/nova.html`
- `templates/vendas/lista.html`
- `templates/vendas/_lista.html`
- `templates/vendas/_form.html`
- `templates/posicao/painel.html`
- `templates/hedge/cenarios.html`
- `templates/hedge/proteger.html`
- `templates/partials/_header.html`
- `templates/partials/_bottom_bar.html`

### Modificar
- `core/settings.py` — AUTH_USER_MODEL, INSTALLED_APPS, MIDDLEWARE, TEMPLATES, sesame, htmx
- `core/urls.py` — include de todos os apps
- `apps/contas/apps.py` — corrigir name para 'apps.contas'
- `apps/safra/apps.py` — corrigir name para 'apps.safra'
- `apps/vendas/apps.py` — corrigir name para 'apps.vendas'
- `apps/posicao/apps.py` — corrigir name para 'apps.posicao'
- `apps/hedge/apps.py` — corrigir name para 'apps.hedge'
- `templates/base.html` — estrutura mobile-first com HTMX + Tailwind CDN

---

## Task 1: Infraestrutura — settings, apps.py, urls, base.html

**Files:**
- Modify: `core/settings.py`
- Modify: `core/urls.py`
- Modify: `apps/contas/apps.py`, `apps/safra/apps.py`, `apps/vendas/apps.py`, `apps/posicao/apps.py`, `apps/hedge/apps.py`
- Modify: `templates/base.html`
- Create: `tests/__init__.py`
- Create: `apps/contas/urls.py` (stub)
- Create: `apps/safra/urls.py` (stub)
- Create: `apps/vendas/urls.py` (stub)
- Create: `apps/posicao/urls.py` (stub com painel)
- Create: `apps/posicao/views.py` (stub)
- Create: `apps/hedge/urls.py` (stub)

> Esta task não tem TDD — é infraestrutura. Teste manual: `python manage.py check` sem erros.

- [ ] **Step 1: Corrigir apps.py de todos os apps**

`apps/contas/apps.py`:
```python
from django.apps import AppConfig

class ContasConfig(AppConfig):
    name = "apps.contas"
    default_auto_field = "django.db.models.BigAutoField"
```

`apps/safra/apps.py`:
```python
from django.apps import AppConfig

class SafraConfig(AppConfig):
    name = "apps.safra"
    default_auto_field = "django.db.models.BigAutoField"
```

`apps/vendas/apps.py`:
```python
from django.apps import AppConfig

class VendasConfig(AppConfig):
    name = "apps.vendas"
    default_auto_field = "django.db.models.BigAutoField"
```

`apps/posicao/apps.py`:
```python
from django.apps import AppConfig

class PosicaoConfig(AppConfig):
    name = "apps.posicao"
    default_auto_field = "django.db.models.BigAutoField"
```

`apps/hedge/apps.py`:
```python
from django.apps import AppConfig

class HedgeConfig(AppConfig):
    name = "apps.hedge"
    default_auto_field = "django.db.models.BigAutoField"
```

- [ ] **Step 2: Reescrever core/settings.py**

```python
from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("SECRET_KEY", default="django-insecure-dev-key-troque-em-producao")
DEBUG = config("DEBUG", default=True, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_htmx",
    "crispy_forms",
    "crispy_tailwind",
    "sesame",
    "apps.contas",
    "apps.safra",
    "apps.vendas",
    "apps.posicao",
    "apps.hedge",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
]

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_USER_MODEL = "contas.Produtor"

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "sesame.backends.ModelBackend",
]

SESAME_MAX_AGE = 60 * 60 * 24

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CRISPY_ALLOWED_TEMPLATE_PACKS = "tailwind"
CRISPY_TEMPLATE_PACK = "tailwind"

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

LOGIN_URL = "/"
LOGIN_REDIRECT_URL = "/painel/"
```

- [ ] **Step 3: Reescrever core/urls.py**

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("", include("apps.contas.urls")),
    path("painel/", include("apps.posicao.urls")),
    path("safra/", include("apps.safra.urls")),
    path("vendas/", include("apps.vendas.urls")),
    path("hedge/", include("apps.hedge.urls")),
    path("admin/", admin.site.urls),
]
```

- [ ] **Step 4: Criar tests/__init__.py**

Criar arquivo vazio em `tests/__init__.py`:
```python
```

- [ ] **Step 4b: Criar stubs de URLs para todos os apps**

`core/urls.py` inclui todos os apps desde o início. Os arquivos de URL precisam existir para `python manage.py check` passar. Criar stubs mínimos agora; as tasks posteriores preenchem o conteúdo real.

`apps/contas/urls.py`:
```python
from django.urls import path

app_name = "contas"
urlpatterns = []
```

`apps/safra/urls.py`:
```python
from django.urls import path

app_name = "safra"
urlpatterns = []
```

`apps/vendas/urls.py`:
```python
from django.urls import path

app_name = "vendas"
urlpatterns = []
```

`apps/posicao/views.py` (stub — substituído na Task 9):
```python
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required


@login_required
def painel(request):
    return HttpResponse("painel em construção")
```

`apps/posicao/urls.py` (stub com painel — necessário para reverse("posicao:painel") nos testes):
```python
from django.urls import path
from . import views

app_name = "posicao"

urlpatterns = [
    path("", views.painel, name="painel"),
]
```

`apps/hedge/urls.py`:
```python
from django.urls import path

app_name = "hedge"
urlpatterns = []
```

- [ ] **Step 5: Escrever templates/base.html**

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
  <title>{% block titulo %}HedgeFácil{% endblock %}</title>
  <script src="https://unpkg.com/htmx.org@2.0.0"></script>
  <script src="https://cdn.tailwindcss.com"></script>
  <link href="https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=DM+Sans:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    body { font-family: 'DM Sans', sans-serif; max-width: 430px; margin: 0 auto; }
    .font-display { font-family: 'Syne', sans-serif; }
    .htmx-indicator { display: none; }
    .htmx-request .htmx-indicator { display: inline; }
    .htmx-request .htmx-indicator-hide { display: none; }
  </style>
</head>
<body class="bg-slate-50 text-slate-900 pb-24">
  {% include "partials/_header.html" %}
  <main class="px-5 py-4">{% block conteudo %}{% endblock %}</main>
  {% include "partials/_bottom_bar.html" %}
</body>
</html>
```

- [ ] **Step 6: Criar templates/partials/_header.html e _bottom_bar.html**

`templates/partials/_header.html`:
```html
<header class="bg-green-800 text-white px-5 py-3 flex justify-between items-center">
  <span class="font-display font-bold text-lg">HedgeFácil</span>
  {% if user.is_authenticated %}
    <a href="/" class="text-sm text-green-200">Sair</a>
  {% endif %}
</header>
```

`templates/partials/_bottom_bar.html`:
```html
{% if user.is_authenticated %}
<nav class="fixed bottom-0 left-1/2 -translate-x-1/2 w-full max-w-[430px] bg-white border-t border-slate-200 flex justify-around py-3">
  <a href="/painel/" class="flex flex-col items-center text-xs text-slate-600">
    <span>📊</span>Posição
  </a>
  <a href="/hedge/{{ safra.id }}/cenarios/" class="flex flex-col items-center text-xs text-slate-600">
    <span>🌱</span>Hedge
  </a>
</nav>
{% endif %}
```

- [ ] **Step 7: Verificar que Django não retorna erros**

```bash
python manage.py check
```

Esperado: `System check identified no issues (0 silenced).`

- [ ] **Step 8: Commit**

```bash
git add core/settings.py core/urls.py apps/*/apps.py templates/ tests/__init__.py
git commit -m "Infra: settings, apps.py, urls, base.html"
```

---

## Task 2: Sessão 1 — Produtor model (TDD)

**Files:**
- Modify: `apps/contas/models.py`
- Modify: `apps/contas/admin.py`
- Modify: `tests/test_modelos.py`

- [ ] **Step 1: Escrever os testes falhando**

`tests/test_modelos.py`:
```python
from django.test import TestCase
from apps.contas.models import Produtor


class ProdutorModelTestCase(TestCase):
    def test_produtor_tem_campo_whatsapp(self):
        p = Produtor.objects.create_user(username="ze", email="ze@test.com")
        self.assertEqual(p.whatsapp, "")

    def test_produtor_tem_campo_cidade(self):
        p = Produtor.objects.create_user(username="ze2", email="ze2@test.com")
        self.assertEqual(p.cidade, "")

    def test_produtor_tem_campo_estado(self):
        p = Produtor.objects.create_user(username="ze3", email="ze3@test.com")
        self.assertEqual(p.estado, "")

    def test_aceitou_termos_nulo_por_padrao(self):
        p = Produtor.objects.create_user(username="ze4", email="ze4@test.com")
        self.assertIsNone(p.aceitou_termos_em)

    def test_produtor_str_retorna_username(self):
        p = Produtor(username="fazendeiro")
        self.assertEqual(str(p), "fazendeiro")
```

- [ ] **Step 2: Rodar os testes para verificar que FALHAM**

```bash
python manage.py test tests.test_modelos
```

Esperado: `ImportError` ou `django.core.exceptions.ImproperlyConfigured` porque Produtor ainda não existe e não há migration.

- [ ] **Step 3: Implementar Produtor model**

`apps/contas/models.py`:
```python
from django.contrib.auth.models import AbstractUser
from django.db import models


class Produtor(AbstractUser):
    whatsapp = models.CharField(max_length=20, blank=True)
    cidade = models.CharField(max_length=100, blank=True)
    estado = models.CharField(max_length=2, blank=True)
    aceitou_termos_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Produtor"
        verbose_name_plural = "Produtores"
```

- [ ] **Step 4: Registrar no admin**

`apps/contas/admin.py`:
```python
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Produtor


@admin.register(Produtor)
class ProdutorAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Dados do Produtor", {"fields": ("whatsapp", "cidade", "estado", "aceitou_termos_em")}),
    )
```

- [ ] **Step 5: Criar e rodar migrations**

```bash
python manage.py makemigrations contas
python manage.py migrate
```

Esperado: migration criada em `apps/contas/migrations/0001_initial.py`, migrate sem erros.

- [ ] **Step 6: Rodar testes para verificar que PASSAM**

```bash
python manage.py test tests.test_modelos
```

Esperado: `OK` com 5 testes passando.

- [ ] **Step 7: Commit**

```bash
git add apps/contas/models.py apps/contas/admin.py apps/contas/migrations/ tests/test_modelos.py
git commit -m "feat: Produtor model com campos extras (TDD)"
```

---

## Task 3: Sessão 2 — Login mágico (TDD)

**Files:**
- Create: `apps/contas/views.py`
- Modify: `apps/contas/urls.py` (preencher stub criado na Task 1)
- Create: `templates/contas/login.html`
- Create: `templates/contas/email_enviado.html`
- Modify: `apps/contas/tests.py`

- [ ] **Step 1: Escrever os testes falhando**

`apps/contas/tests.py`:
```python
from django.test import TestCase
from django.urls import reverse
from django.core import mail
from apps.contas.models import Produtor


class LoginMagicoTestCase(TestCase):
    def test_get_login_retorna_200(self):
        response = self.client.get(reverse("contas:login"))
        self.assertEqual(response.status_code, 200)

    def test_post_login_cria_produtor_se_nao_existe(self):
        self.client.post(reverse("contas:login"), {"email": "novo@test.com"})
        self.assertTrue(Produtor.objects.filter(email="novo@test.com").exists())

    def test_post_login_nao_duplica_produtor_existente(self):
        Produtor.objects.create_user(username="ze@test.com", email="ze@test.com")
        self.client.post(reverse("contas:login"), {"email": "ze@test.com"})
        self.assertEqual(Produtor.objects.filter(email="ze@test.com").count(), 1)

    def test_post_login_envia_email(self):
        self.client.post(reverse("contas:login"), {"email": "ze@test.com"})
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("ze@test.com", mail.outbox[0].to)

    def test_post_login_redireciona_para_confirmacao(self):
        response = self.client.post(reverse("contas:login"), {"email": "ze@test.com"})
        self.assertRedirects(response, reverse("contas:email_enviado"))

    def test_email_enviado_retorna_200(self):
        response = self.client.get(reverse("contas:email_enviado"))
        self.assertEqual(response.status_code, 200)
```

- [ ] **Step 2: Rodar para verificar que FALHAM**

```bash
python manage.py test apps.contas
```

Esperado: `NoReverseMatch` — URLs não existem ainda.

- [ ] **Step 3: Criar urls.py de contas**

`apps/contas/urls.py`:
```python
from django.urls import path
from . import views

app_name = "contas"

urlpatterns = [
    path("", views.solicitar_login, name="login"),
    path("email-enviado/", views.email_enviado, name="email_enviado"),
]
```

- [ ] **Step 4: Criar views.py de contas**

`apps/contas/views.py`:
```python
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from sesame.utils import get_query_string
from .models import Produtor


def solicitar_login(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        if email:
            produtor, _ = Produtor.objects.get_or_create(
                email=email,
                defaults={"username": email},
            )
            link = request.build_absolute_uri("/painel/") + get_query_string(produtor)
            send_mail(
                "Acesso HedgeFácil",
                f"Acesse: {link}",
                "no-reply@hedgefacil.com.br",
                [email],
            )
        return redirect("contas:email_enviado")
    return render(request, "contas/login.html")


def email_enviado(request):
    return render(request, "contas/email_enviado.html")
```

- [ ] **Step 5: Criar templates mínimos**

`templates/contas/login.html`:
```html
{% extends "base.html" %}
{% block conteudo %}
<h1 class="font-display text-2xl font-bold text-green-800 mb-6">Entrar no HedgeFácil</h1>
<form method="post" class="space-y-4">
  {% csrf_token %}
  <div>
    <label class="block text-sm font-medium text-slate-700 mb-1">Seu email</label>
    <input type="email" name="email" required
           class="w-full border border-slate-300 rounded-lg px-4 py-3 text-base"
           placeholder="produtor@email.com">
  </div>
  <button type="submit"
          class="w-full bg-green-700 text-white rounded-lg py-4 font-semibold text-base min-h-[48px]">
    Receber link de acesso
  </button>
</form>
{% endblock %}
```

`templates/contas/email_enviado.html`:
```html
{% extends "base.html" %}
{% block conteudo %}
<div class="text-center py-12">
  <p class="text-4xl mb-4">📬</p>
  <h1 class="font-display text-2xl font-bold text-green-800 mb-2">Email enviado!</h1>
  <p class="text-slate-600">Verifique sua caixa de entrada e clique no link para entrar.</p>
</div>
{% endblock %}
```

- [ ] **Step 6: Ajustar EMAIL_BACKEND para testes**

Adicionar em `core/settings.py` (já está como console, mas confirmar):
```python
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
```

Em testes, Django substitui o backend automaticamente por `django.test.mail.outbox`.

- [ ] **Step 7: Rodar testes para verificar que PASSAM**

```bash
python manage.py test apps.contas
```

Esperado: `OK` com 6 testes passando.

- [ ] **Step 8: Commit**

```bash
git add apps/contas/views.py apps/contas/urls.py apps/contas/tests.py templates/contas/
git commit -m "feat: login mágico por email com django-sesame (TDD)"
```

---

## Task 4: Sessão 4 — Safra model (TDD)

**Files:**
- Modify: `apps/safra/models.py`
- Modify: `apps/safra/admin.py`
- Create: `apps/safra/forms.py`
- Create: `apps/safra/views.py`
- Modify: `apps/safra/urls.py` (preencher stub criado na Task 1)
- Create: `templates/safra/nova.html`
- Modify: `tests/test_modelos.py`

- [ ] **Step 1: Escrever testes do model Safra**

Adicionar ao final de `tests/test_modelos.py`:
```python
from decimal import Decimal
from apps.safra.models import Safra


class SafraModelTestCase(TestCase):
    def setUp(self):
        self.produtor = Produtor.objects.create_user(username="fazendeiro", email="f@test.com")

    def test_custo_total_multiplica_producao_por_custo(self):
        safra = Safra(
            producao_estimada_sacas=Decimal("1000"),
            custo_por_saca=Decimal("80"),
        )
        self.assertEqual(safra.custo_total, Decimal("80000"))

    def test_custo_total_usa_decimal(self):
        safra = Safra(
            producao_estimada_sacas=Decimal("1000"),
            custo_por_saca=Decimal("80.50"),
        )
        self.assertIsInstance(safra.custo_total, Decimal)

    def test_str_contem_cultura_e_ano(self):
        safra = Safra(
            cultura="soja",
            ano_safra="2025/26",
            producao_estimada_sacas=Decimal("1000"),
            custo_por_saca=Decimal("80"),
        )
        safra.produtor = self.produtor
        self.assertIn("Soja", str(safra))
        self.assertIn("2025/26", str(safra))

    def test_unique_produtor_cultura_ano(self):
        from django.db import IntegrityError
        Safra.objects.create(
            produtor=self.produtor, cultura="soja", ano_safra="2025/26",
            producao_estimada_sacas=Decimal("1000"), custo_por_saca=Decimal("80"),
        )
        with self.assertRaises(IntegrityError):
            Safra.objects.create(
                produtor=self.produtor, cultura="soja", ano_safra="2025/26",
                producao_estimada_sacas=Decimal("500"), custo_por_saca=Decimal("90"),
            )
```

- [ ] **Step 2: Rodar para verificar que FALHAM**

```bash
python manage.py test tests.test_modelos.SafraModelTestCase
```

Esperado: `ImportError` — Safra não existe.

- [ ] **Step 3: Implementar Safra model**

`apps/safra/models.py`:
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
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("produtor", "cultura", "ano_safra")]
        ordering = ["-criada_em"]

    def __str__(self):
        return f"{self.get_cultura_display()} {self.ano_safra} — {self.produtor.username}"

    @property
    def custo_total(self) -> Decimal:
        return self.producao_estimada_sacas * self.custo_por_saca
```

- [ ] **Step 4: Registrar no admin**

`apps/safra/admin.py`:
```python
from django.contrib import admin
from .models import Safra


@admin.register(Safra)
class SafraAdmin(admin.ModelAdmin):
    list_display = ["produtor", "cultura", "ano_safra", "producao_estimada_sacas", "ativa"]
    list_filter = ["cultura", "ativa"]
```

- [ ] **Step 5: Migrations**

```bash
python manage.py makemigrations safra
python manage.py migrate
```

Esperado: migration criada, migrate sem erros.

- [ ] **Step 6: Rodar testes para verificar que PASSAM**

```bash
python manage.py test tests.test_modelos.SafraModelTestCase
```

Esperado: `OK` com 4 testes passando.

- [ ] **Step 7: Criar form e view de nova safra**

`apps/safra/forms.py`:
```python
from django import forms
from .models import Safra


class SafraForm(forms.ModelForm):
    class Meta:
        model = Safra
        fields = ["cultura", "ano_safra", "producao_estimada_sacas", "custo_por_saca", "cidade", "estado"]
        widgets = {
            "producao_estimada_sacas": forms.NumberInput(attrs={"placeholder": "Ex: 3000"}),
            "custo_por_saca": forms.NumberInput(attrs={"placeholder": "Ex: 80.00"}),
            "ano_safra": forms.TextInput(attrs={"placeholder": "Ex: 2025/26"}),
        }
```

`apps/safra/views.py`:
```python
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import SafraForm


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
    return render(request, "safra/nova.html", {"form": form})
```

`apps/safra/urls.py`:
```python
from django.urls import path
from . import views

app_name = "safra"

urlpatterns = [
    path("nova/", views.nova, name="nova"),
]
```

`templates/safra/nova.html`:
```html
{% extends "base.html" %}
{% block conteudo %}
<h1 class="font-display text-2xl font-bold text-green-800 mb-6">Nova Safra</h1>
<form method="post" class="space-y-4">
  {% csrf_token %}
  {{ form.as_p }}
  <button type="submit"
          class="w-full bg-green-700 text-white rounded-lg py-4 font-semibold min-h-[48px]">
    Salvar Safra
  </button>
</form>
{% endblock %}
```

- [ ] **Step 8: Commit**

```bash
git add apps/safra/ tests/test_modelos.py templates/safra/
git commit -m "feat: Safra model + form + view nova (TDD)"
```

---

## Task 5: Sessão 5 — Venda model (TDD)

**Files:**
- Modify: `apps/vendas/models.py`
- Modify: `apps/vendas/admin.py`
- Modify: `tests/test_modelos.py`

- [ ] **Step 1: Escrever testes do model Venda**

Adicionar ao final de `tests/test_modelos.py`:
```python
import datetime
from apps.vendas.models import Venda


class VendaModelTestCase(TestCase):
    def setUp(self):
        self.produtor = Produtor.objects.create_user(username="vend_test", email="vt@test.com")
        self.safra = Safra.objects.create(
            produtor=self.produtor,
            cultura="soja",
            ano_safra="2025/26",
            producao_estimada_sacas=Decimal("1000"),
            custo_por_saca=Decimal("80"),
        )

    def test_receita_multiplica_sacas_por_preco(self):
        venda = Venda(sacas=Decimal("300"), preco_por_saca=Decimal("120"))
        self.assertEqual(venda.receita, Decimal("36000"))

    def test_receita_usa_decimal_nao_float(self):
        venda = Venda(sacas=Decimal("300"), preco_por_saca=Decimal("120.50"))
        self.assertIsInstance(venda.receita, Decimal)

    def test_receita_com_valor_decimal_fracionado(self):
        venda = Venda(sacas=Decimal("300"), preco_por_saca=Decimal("120.50"))
        self.assertEqual(venda.receita, Decimal("36150.00"))

    def test_str_contem_contraparte_e_sacas(self):
        venda = Venda(
            contraparte="Cargill",
            sacas=Decimal("300"),
            preco_por_saca=Decimal("120"),
        )
        resultado = str(venda)
        self.assertIn("Cargill", resultado)
        self.assertIn("300", resultado)
```

- [ ] **Step 2: Rodar para verificar que FALHAM**

```bash
python manage.py test tests.test_modelos.VendaModelTestCase
```

Esperado: `ImportError` — Venda não existe.

- [ ] **Step 3: Implementar Venda model**

`apps/vendas/models.py`:
```python
from decimal import Decimal
from django.db import models


class TipoVenda(models.TextChoices):
    TERMO = "termo", "Contrato a Termo"
    CPR = "cpr", "CPR (Cédula de Produto Rural)"
    BALCAO = "balcao", "Venda Balcão"
    FUTURO_B3 = "futuro_b3", "Futuro B3"
    OPCAO_B3 = "opcao_b3", "Opção B3"


class Venda(models.Model):
    safra = models.ForeignKey(
        "safra.Safra",
        on_delete=models.CASCADE,
        related_name="vendas",
    )
    tipo = models.CharField(max_length=20, choices=TipoVenda.choices)
    contraparte = models.CharField(max_length=120, help_text="Cargill, Coopercitrus, BB, etc.")
    sacas = models.DecimalField(max_digits=12, decimal_places=2)
    preco_por_saca = models.DecimalField(max_digits=10, decimal_places=2)
    data_negociacao = models.DateField()
    observacao = models.TextField(blank=True)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-data_negociacao"]

    def __str__(self):
        return f"{self.contraparte} — {self.sacas} sc @ R$ {self.preco_por_saca}"

    @property
    def receita(self) -> Decimal:
        return self.sacas * self.preco_por_saca
```

- [ ] **Step 4: Admin**

`apps/vendas/admin.py`:
```python
from django.contrib import admin
from .models import Venda


@admin.register(Venda)
class VendaAdmin(admin.ModelAdmin):
    list_display = ["contraparte", "safra", "tipo", "sacas", "preco_por_saca", "data_negociacao"]
    list_filter = ["tipo"]
    date_hierarchy = "data_negociacao"
```

- [ ] **Step 5: Migrations**

```bash
python manage.py makemigrations vendas
python manage.py migrate
```

- [ ] **Step 6: Rodar testes para verificar que PASSAM**

```bash
python manage.py test tests.test_modelos.VendaModelTestCase
```

Esperado: `OK` com 4 testes passando.

- [ ] **Step 7: Rodar todos os testes para verificar nenhuma regressão**

```bash
python manage.py test tests
```

Esperado: todos os testes passando.

- [ ] **Step 8: Commit**

```bash
git add apps/vendas/models.py apps/vendas/admin.py apps/vendas/migrations/ tests/test_modelos.py
git commit -m "feat: Venda model com property receita (TDD)"
```

---

## Task 6: Sessão 6 — CRUD Venda views (TDD)

**Files:**
- Create: `apps/vendas/forms.py`
- Modify: `apps/vendas/views.py`
- Modify: `apps/vendas/urls.py` (preencher stub criado na Task 1)
- Create: `templates/vendas/lista.html`
- Create: `templates/vendas/_lista.html`
- Create: `templates/vendas/_form.html`
- Modify: `apps/vendas/tests.py`

- [ ] **Step 1: Escrever testes de views de vendas**

`apps/vendas/tests.py`:
```python
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from apps.contas.models import Produtor
from apps.safra.models import Safra
from apps.vendas.models import Venda


class VendasViewsTestCase(TestCase):
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

    def test_lista_vendas_retorna_200(self):
        response = self.client.get(reverse("vendas:lista", args=[self.safra.id]))
        self.assertEqual(response.status_code, 200)

    def test_lista_vendas_requer_login(self):
        self.client.logout()
        response = self.client.get(reverse("vendas:lista", args=[self.safra.id]))
        self.assertEqual(response.status_code, 302)

    def test_nova_venda_get_retorna_200(self):
        response = self.client.get(reverse("vendas:nova", args=[self.safra.id]))
        self.assertEqual(response.status_code, 200)

    def test_nova_venda_post_valido_cria_venda(self):
        data = {
            "tipo": "balcao",
            "contraparte": "Cargill",
            "sacas": "300",
            "preco_por_saca": "120.50",
            "data_negociacao": "2025-03-01",
        }
        self.client.post(reverse("vendas:nova", args=[self.safra.id]), data)
        self.assertEqual(Venda.objects.count(), 1)

    def test_nova_venda_post_valido_redireciona(self):
        data = {
            "tipo": "balcao",
            "contraparte": "Cargill",
            "sacas": "300",
            "preco_por_saca": "120.50",
            "data_negociacao": "2025-03-01",
        }
        response = self.client.post(reverse("vendas:nova", args=[self.safra.id]), data)
        self.assertRedirects(response, reverse("posicao:painel"))

    def test_nova_venda_post_invalido_nao_cria_venda(self):
        response = self.client.post(reverse("vendas:nova", args=[self.safra.id]), {})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Venda.objects.exists())

    def test_lista_nao_mostra_vendas_de_outros_produtores(self):
        outro = Produtor.objects.create_user(username="outro", email="outro@test.com")
        safra_outro = Safra.objects.create(
            produtor=outro, cultura="milho", ano_safra="2025/26",
            producao_estimada_sacas=Decimal("500"), custo_por_saca=Decimal("60"),
        )
        Venda.objects.create(
            safra=safra_outro, tipo="balcao", contraparte="Bunge",
            sacas=Decimal("100"), preco_por_saca=Decimal("50"),
            data_negociacao="2025-01-01",
        )
        response = self.client.get(reverse("vendas:lista", args=[self.safra.id]))
        self.assertNotContains(response, "Bunge")
```

- [ ] **Step 2: Rodar para verificar que FALHAM**

```bash
python manage.py test apps.vendas
```

Esperado: `NoReverseMatch` — URLs não existem.

- [ ] **Step 3: Criar form de Venda**

`apps/vendas/forms.py`:
```python
from django import forms
from .models import Venda


class VendaForm(forms.ModelForm):
    class Meta:
        model = Venda
        fields = ["tipo", "contraparte", "sacas", "preco_por_saca", "data_negociacao", "observacao"]
        widgets = {
            "data_negociacao": forms.DateInput(attrs={"type": "date"}),
            "sacas": forms.NumberInput(attrs={"placeholder": "Ex: 500"}),
            "preco_por_saca": forms.NumberInput(attrs={"placeholder": "Ex: 125.00", "step": "0.01"}),
        }
```

- [ ] **Step 4: Criar views de Venda**

`apps/vendas/views.py`:
```python
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from apps.safra.models import Safra
from .models import Venda
from .forms import VendaForm


@login_required
def lista(request, safra_id):
    safra = get_object_or_404(Safra, id=safra_id, produtor=request.user)
    vendas = safra.vendas.all()
    return render(request, "vendas/lista.html", {"vendas": vendas, "safra": safra})


@login_required
def nova(request, safra_id):
    safra = get_object_or_404(Safra, id=safra_id, produtor=request.user)
    if request.method == "POST":
        form = VendaForm(request.POST)
        if form.is_valid():
            venda = form.save(commit=False)
            venda.safra = safra
            venda.save()
            if request.htmx:
                return render(request, "vendas/_lista.html", {"vendas": safra.vendas.all(), "safra": safra})
            return redirect("posicao:painel")
    else:
        form = VendaForm()
    return render(request, "vendas/_form.html", {"form": form, "safra": safra})
```

- [ ] **Step 5: Criar urls.py de vendas**

`apps/vendas/urls.py`:
```python
from django.urls import path
from . import views

app_name = "vendas"

urlpatterns = [
    path("<int:safra_id>/", views.lista, name="lista"),
    path("nova/<int:safra_id>/", views.nova, name="nova"),
]
```

- [ ] **Step 6: Criar templates de vendas**

`templates/vendas/lista.html`:
```html
{% extends "base.html" %}
{% block conteudo %}
<div class="flex justify-between items-center mb-4">
  <h1 class="font-display text-xl font-bold text-green-800">Vendas — {{ safra }}</h1>
  <a href="{% url 'vendas:nova' safra.id %}"
     class="bg-green-700 text-white px-4 py-2 rounded-lg text-sm font-semibold">
    + Nova
  </a>
</div>
<div id="lista-vendas">
  {% include "vendas/_lista.html" %}
</div>
{% endblock %}
```

`templates/vendas/_lista.html`:
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
</div>
{% empty %}
<p class="text-slate-500 text-center py-8">Nenhuma venda lançada ainda.</p>
{% endfor %}
```

`templates/vendas/_form.html`:
```html
{% extends "base.html" %}
{% block conteudo %}
<h1 class="font-display text-xl font-bold text-green-800 mb-4">Nova Venda</h1>
<form method="post" class="space-y-4"
      hx-post="{% url 'vendas:nova' safra.id %}"
      hx-target="#lista-vendas"
      hx-swap="outerHTML">
  {% csrf_token %}
  {{ form.as_p }}
  <button type="submit"
          class="w-full bg-green-700 text-white rounded-lg py-4 font-semibold min-h-[48px]">
    <span class="htmx-indicator-hide">Salvar venda</span>
    <span class="htmx-indicator">Salvando...</span>
  </button>
</form>
{% endblock %}
```

- [ ] **Step 7: Rodar testes para verificar que PASSAM**

```bash
python manage.py test apps.vendas
```

Esperado: `OK` com 7 testes passando.

- [ ] **Step 8: Commit**

```bash
git add apps/vendas/ templates/vendas/
git commit -m "feat: CRUD de Venda com views e templates (TDD)"
```

---

## Task 7: Sessão 7 — HTMX fragmentos (TDD)

**Files:**
- Modify: `apps/vendas/tests.py`

> Esta task adiciona testes HTMX à suite existente. O código já está implementado na Task 6. Aqui validamos o comportamento HTMX.

- [ ] **Step 1: Escrever testes HTMX falhando**

Adicionar à classe `VendasViewsTestCase` em `apps/vendas/tests.py`:
```python
    def test_htmx_post_valido_retorna_fragmento(self):
        data = {
            "tipo": "balcao",
            "contraparte": "Cargill",
            "sacas": "300",
            "preco_por_saca": "120.50",
            "data_negociacao": "2025-03-01",
        }
        response = self.client.post(
            reverse("vendas:nova", args=[self.safra.id]),
            data,
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "vendas/_lista.html")

    def test_htmx_post_valido_nao_redireciona(self):
        data = {
            "tipo": "balcao",
            "contraparte": "Cargill",
            "sacas": "300",
            "preco_por_saca": "120.50",
            "data_negociacao": "2025-03-01",
        }
        response = self.client.post(
            reverse("vendas:nova", args=[self.safra.id]),
            data,
            HTTP_HX_REQUEST="true",
        )
        self.assertNotEqual(response.status_code, 302)

    def test_post_normal_redireciona_nao_retorna_fragmento(self):
        data = {
            "tipo": "balcao",
            "contraparte": "Cargill",
            "sacas": "300",
            "preco_por_saca": "120.50",
            "data_negociacao": "2025-03-01",
        }
        response = self.client.post(reverse("vendas:nova", args=[self.safra.id]), data)
        self.assertEqual(response.status_code, 302)
```

- [ ] **Step 2: Rodar para verificar que FALHAM**

```bash
python manage.py test apps.vendas.tests.VendasViewsTestCase.test_htmx_post_valido_retorna_fragmento
```

Esperado: `AssertionError` — retorna 302 em vez de 200 (HTMX não detectado ainda).

- [ ] **Step 3: Verificar que HtmxMiddleware está em MIDDLEWARE**

Confirmar em `core/settings.py`:
```python
"django_htmx.middleware.HtmxMiddleware",
```

O middleware popula `request.htmx` como objeto truthy quando o header `HX-Request: true` está presente. O `HTTP_HX_REQUEST="true"` no cliente de teste simula esse header.

- [ ] **Step 4: Rodar todos os testes de vendas para verificar que PASSAM**

```bash
python manage.py test apps.vendas
```

Esperado: `OK` com 10 testes passando (7 anteriores + 3 novos).

- [ ] **Step 5: Commit**

```bash
git add apps/vendas/tests.py
git commit -m "test: adiciona cobertura HTMX em vendas (TDD)"
```

---

## Task 8: Sessão 8 — posicao/services.py (TDD — crítico)

**Files:**
- Create: `apps/posicao/services.py`
- Modify: `tests/test_calculos.py`

> Esta é a task mais crítica — cálculo errado = produtor toma decisão errada.

- [ ] **Step 1: Escrever todos os testes de calcular_posicao**

`tests/test_calculos.py`:
```python
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
```

- [ ] **Step 2: Rodar para verificar que FALHAM**

```bash
python manage.py test tests.test_calculos
```

Esperado: `ImportError` — calcular_posicao não existe.

- [ ] **Step 3: Implementar posicao/services.py**

`apps/posicao/services.py`:
```python
from decimal import Decimal
from dataclasses import dataclass
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
```

- [ ] **Step 4: Rodar testes para verificar que PASSAM**

```bash
python manage.py test tests.test_calculos.CalcularPosicaoTestCase
```

Esperado: `OK` com 11 testes passando.

- [ ] **Step 5: Rodar toda a suite para checar regressões**

```bash
python manage.py test tests apps.contas apps.vendas
```

Esperado: todos passando.

- [ ] **Step 6: Commit**

```bash
git add apps/posicao/services.py tests/test_calculos.py
git commit -m "feat: calcular_posicao service com 11 testes (TDD crítico)"
```

---

## Task 9: Sessão 9 — View /painel/ (TDD)

**Files:**
- Modify: `apps/posicao/views.py` (substituir stub da Task 1)
- Modify: `apps/posicao/urls.py` (já tem painel, sem mudança necessária)
- Create: `templates/posicao/painel.html`
- Create: `apps/posicao/tests.py`

- [ ] **Step 1: Escrever testes da view painel**

`apps/posicao/tests.py`:
```python
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from apps.contas.models import Produtor
from apps.safra.models import Safra


class PainelViewTestCase(TestCase):
    def setUp(self):
        self.produtor = Produtor.objects.create_user(
            username="ze", email="ze@test.com", password="senha123"
        )
        self.client.force_login(self.produtor)

    def test_painel_requer_login(self):
        self.client.logout()
        response = self.client.get(reverse("posicao:painel"))
        self.assertEqual(response.status_code, 302)

    def test_painel_sem_safra_redireciona_para_nova_safra(self):
        response = self.client.get(reverse("posicao:painel"))
        self.assertRedirects(response, reverse("safra:nova"))

    def test_painel_com_safra_retorna_200(self):
        Safra.objects.create(
            produtor=self.produtor,
            cultura="soja",
            ano_safra="2025/26",
            producao_estimada_sacas=Decimal("1000"),
            custo_por_saca=Decimal("80"),
        )
        response = self.client.get(reverse("posicao:painel"))
        self.assertEqual(response.status_code, 200)

    def test_painel_contexto_tem_posicao(self):
        Safra.objects.create(
            produtor=self.produtor,
            cultura="soja",
            ano_safra="2025/26",
            producao_estimada_sacas=Decimal("1000"),
            custo_por_saca=Decimal("80"),
        )
        response = self.client.get(reverse("posicao:painel"))
        self.assertIn("posicao", response.context)

    def test_painel_contexto_tem_safra(self):
        safra = Safra.objects.create(
            produtor=self.produtor,
            cultura="soja",
            ano_safra="2025/26",
            producao_estimada_sacas=Decimal("1000"),
            custo_por_saca=Decimal("80"),
        )
        response = self.client.get(reverse("posicao:painel"))
        self.assertEqual(response.context["safra"], safra)

    def test_painel_nao_mostra_safra_de_outro_produtor(self):
        outro = Produtor.objects.create_user(username="outro", email="outro@test.com")
        Safra.objects.create(
            produtor=outro,
            cultura="milho",
            ano_safra="2025/26",
            producao_estimada_sacas=Decimal("500"),
            custo_por_saca=Decimal("60"),
        )
        response = self.client.get(reverse("posicao:painel"))
        self.assertRedirects(response, reverse("safra:nova"))
```

- [ ] **Step 2: Rodar para verificar que FALHAM**

```bash
python manage.py test apps.posicao
```

Esperado: `NoReverseMatch` — posicao:painel não existe.

- [ ] **Step 3: Implementar view e urls de posição**

`apps/posicao/urls.py`:
```python
from django.urls import path
from . import views

app_name = "posicao"

urlpatterns = [
    path("", views.painel, name="painel"),
]
```

`apps/posicao/views.py`:
```python
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from apps.safra.models import Safra
from .services import calcular_posicao


@login_required
def painel(request):
    safra = Safra.objects.filter(produtor=request.user, ativa=True).first()
    if not safra:
        return redirect("safra:nova")
    posicao = calcular_posicao(safra)
    return render(request, "posicao/painel.html", {"posicao": posicao, "safra": safra})
```

- [ ] **Step 4: Criar template do painel**

`templates/posicao/painel.html`:
```html
{% extends "base.html" %}
{% block conteudo %}
<div class="mb-6">
  <p class="text-sm text-slate-500">{{ safra }}</p>
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

<a href="{% url 'vendas:lista' safra.id %}"
   class="block w-full bg-green-700 text-white text-center rounded-xl py-4 font-semibold min-h-[48px]">
  Ver vendas
</a>
<a href="{% url 'hedge:cenarios' safra.id %}"
   class="block w-full border border-green-700 text-green-700 text-center rounded-xl py-4 font-semibold mt-3 min-h-[48px]">
  Simular cenários
</a>
{% endblock %}
```

- [ ] **Step 5: Rodar testes para verificar que PASSAM**

```bash
python manage.py test apps.posicao
```

Esperado: `OK` com 6 testes passando.

- [ ] **Step 6: Commit**

```bash
git add apps/posicao/ templates/posicao/
git commit -m "feat: view /painel/ com calcular_posicao (TDD)"
```

---

## Task 10: Sessão 10 — hedge/services.py (TDD puro)

**Files:**
- Create: `apps/hedge/services.py`
- Modify: `tests/test_calculos.py`

> `simular_cenarios` é função pura — usa `unittest.TestCase` sem banco.

- [ ] **Step 1: Escrever testes puros de simular_cenarios**

Adicionar ao final de `tests/test_calculos.py`:
```python
import unittest
from apps.hedge.services import simular_cenarios


class SimularCenariosTestCase(unittest.TestCase):
    def test_retorna_3_cenarios_por_padrao(self):
        cenarios = simular_cenarios(
            sacas_a_vender=Decimal("700"),
            preco_atual=Decimal("130"),
        )
        self.assertEqual(len(cenarios), 3)

    def test_cenario_estavel_variacao_zero(self):
        cenarios = simular_cenarios(
            sacas_a_vender=Decimal("700"),
            preco_atual=Decimal("130"),
        )
        estavel = next(c for c in cenarios if c.variacao_percentual == Decimal("0"))
        self.assertEqual(estavel.impacto_vs_atual, Decimal("0.00"))

    def test_cenario_queda_20_preco_projetado_correto(self):
        cenarios = simular_cenarios(
            sacas_a_vender=Decimal("700"),
            preco_atual=Decimal("130"),
        )
        queda = next(c for c in cenarios if c.variacao_percentual == Decimal("-20"))
        # 130 * 0.80 = 104.00
        self.assertEqual(queda.preco_projetado, Decimal("104.00"))

    def test_cenario_queda_20_receita_correta(self):
        cenarios = simular_cenarios(
            sacas_a_vender=Decimal("700"),
            preco_atual=Decimal("130"),
        )
        queda = next(c for c in cenarios if c.variacao_percentual == Decimal("-20"))
        # 700 * 104 = 72800
        self.assertEqual(queda.receita_no_saldo, Decimal("72800.00"))

    def test_cenario_queda_impacto_negativo(self):
        cenarios = simular_cenarios(
            sacas_a_vender=Decimal("700"),
            preco_atual=Decimal("130"),
        )
        queda = next(c for c in cenarios if c.variacao_percentual == Decimal("-20"))
        self.assertLess(queda.impacto_vs_atual, Decimal("0"))

    def test_cenario_alta_15_preco_projetado_correto(self):
        cenarios = simular_cenarios(
            sacas_a_vender=Decimal("700"),
            preco_atual=Decimal("130"),
        )
        alta = next(c for c in cenarios if c.variacao_percentual == Decimal("15"))
        # 130 * 1.15 = 149.50
        self.assertEqual(alta.preco_projetado, Decimal("149.50"))

    def test_cenario_alta_15_receita_correta(self):
        cenarios = simular_cenarios(
            sacas_a_vender=Decimal("700"),
            preco_atual=Decimal("130"),
        )
        alta = next(c for c in cenarios if c.variacao_percentual == Decimal("15"))
        # 700 * 149.50 = 104650
        self.assertEqual(alta.receita_no_saldo, Decimal("104650.00"))

    def test_cenario_alta_impacto_positivo(self):
        cenarios = simular_cenarios(
            sacas_a_vender=Decimal("700"),
            preco_atual=Decimal("130"),
        )
        alta = next(c for c in cenarios if c.variacao_percentual == Decimal("15"))
        self.assertGreater(alta.impacto_vs_atual, Decimal("0"))

    def test_todos_precos_projetados_sao_decimal(self):
        cenarios = simular_cenarios(
            sacas_a_vender=Decimal("700"),
            preco_atual=Decimal("130"),
        )
        for c in cenarios:
            self.assertIsInstance(c.preco_projetado, Decimal)
            self.assertIsInstance(c.receita_no_saldo, Decimal)
            self.assertIsInstance(c.impacto_vs_atual, Decimal)

    def test_variacoes_customizadas(self):
        from decimal import Decimal as D
        cenarios = simular_cenarios(
            sacas_a_vender=D("500"),
            preco_atual=D("100"),
            variacoes=[D("-10"), D("10")],
        )
        self.assertEqual(len(cenarios), 2)
```

- [ ] **Step 2: Rodar para verificar que FALHAM**

```bash
python manage.py test tests.test_calculos.SimularCenariosTestCase
```

Esperado: `ImportError` — simular_cenarios não existe.

- [ ] **Step 3: Implementar hedge/services.py**

`apps/hedge/services.py`:
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
    Decimal("-20"): "Preço cai 20%",
    Decimal("0"): "Preço fica igual",
    Decimal("15"): "Preço sobe 15%",
}


def simular_cenarios(
    sacas_a_vender: Decimal,
    preco_atual: Decimal,
    variacoes: list[Decimal] = None,
) -> list[CenarioPreco]:
    if variacoes is None:
        variacoes = [Decimal("-20"), Decimal("0"), Decimal("15")]

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

- [ ] **Step 4: Rodar testes para verificar que PASSAM**

```bash
python manage.py test tests.test_calculos
```

Esperado: `OK` com todos os testes de cálculo passando (11 posicao + 10 hedge).

- [ ] **Step 5: Commit**

```bash
git add apps/hedge/services.py tests/test_calculos.py
git commit -m "feat: simular_cenarios service com 10 testes (TDD puro)"
```

---

## Task 11: Sessão 11 — Views de hedge (TDD)

**Files:**
- Modify: `apps/hedge/views.py`
- Modify: `apps/hedge/urls.py` (preencher stub criado na Task 1)
- Create: `templates/hedge/cenarios.html`
- Create: `templates/hedge/proteger.html`
- Modify: `apps/hedge/tests.py`

- [ ] **Step 1: Escrever testes das views de hedge**

`apps/hedge/tests.py`:
```python
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from apps.contas.models import Produtor
from apps.safra.models import Safra


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

    def test_cenarios_contexto_tem_3_cenarios(self):
        response = self.client.get(reverse("hedge:cenarios", args=[self.safra.id]))
        self.assertEqual(len(response.context["cenarios"]), 3)

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
```

- [ ] **Step 2: Rodar para verificar que FALHAM**

```bash
python manage.py test apps.hedge
```

Esperado: `NoReverseMatch` — hedge:cenarios não existe.

- [ ] **Step 3: Criar urls.py de hedge**

`apps/hedge/urls.py`:
```python
from django.urls import path
from . import views

app_name = "hedge"

urlpatterns = [
    path("<int:safra_id>/cenarios/", views.cenarios, name="cenarios"),
    path("<int:safra_id>/proteger/", views.proteger, name="proteger"),
]
```

- [ ] **Step 4: Implementar views de hedge**

`apps/hedge/views.py`:
```python
from decimal import Decimal
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from apps.safra.models import Safra
from apps.posicao.services import calcular_posicao
from .services import simular_cenarios


@login_required
def cenarios(request, safra_id):
    safra = get_object_or_404(Safra, id=safra_id, produtor=request.user)
    posicao = calcular_posicao(safra)
    preco_atual = Decimal(request.GET.get("preco_atual", "130"))
    lista_cenarios = simular_cenarios(
        sacas_a_vender=posicao.sacas_a_vender,
        preco_atual=preco_atual,
    )
    return render(request, "hedge/cenarios.html", {
        "cenarios": lista_cenarios,
        "safra": safra,
        "posicao": posicao,
        "preco_atual": preco_atual,
    })


@login_required
def proteger(request, safra_id):
    safra = get_object_or_404(Safra, id=safra_id, produtor=request.user)
    return render(request, "hedge/proteger.html", {"safra": safra})
```

- [ ] **Step 5: Criar templates de hedge**

`templates/hedge/cenarios.html`:
```html
{% extends "base.html" %}
{% block conteudo %}
<h1 class="font-display text-2xl font-bold text-green-800 mb-2">Cenários de Preço</h1>
<p class="text-sm text-slate-500 mb-4">{{ posicao.sacas_a_vender }} sc a vender · preço atual R$ {{ preco_atual }}</p>

{% for cenario in cenarios %}
<div class="bg-white rounded-xl p-4 mb-3 shadow-sm border border-slate-100">
  <div class="flex justify-between items-center">
    <span class="font-semibold text-slate-800">{{ cenario.nome }}</span>
    <span class="font-display text-lg font-bold {% if cenario.impacto_vs_atual > 0 %}text-green-700{% elif cenario.impacto_vs_atual < 0 %}text-red-600{% else %}text-slate-700{% endif %}">
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

`templates/hedge/proteger.html`:
```html
{% extends "base.html" %}
{% block conteudo %}
<h1 class="font-display text-2xl font-bold text-green-800 mb-4">Como se proteger</h1>
<p class="text-slate-600 mb-6">
  Para travar o preço do saldo que ainda vai vender, você pode usar instrumentos de hedge.
  Fale com um especialista para entender qual é o melhor para a sua situação.
</p>
<a href="https://wa.me/5519983052450?text=Olá%2C%20quero%20entender%20como%20fazer%20hedge%20da%20minha%20safra"
   class="block w-full bg-green-700 text-white text-center rounded-xl py-4 font-semibold min-h-[48px]"
   target="_blank">
  Falar no WhatsApp
</a>
{% endblock %}
```

- [ ] **Step 6: Rodar testes para verificar que PASSAM**

```bash
python manage.py test apps.hedge
```

Esperado: `OK` com 7 testes passando.

- [ ] **Step 7: Rodar suite completa**

```bash
python manage.py test tests apps.contas apps.safra apps.vendas apps.posicao apps.hedge
```

Esperado: todos passando, nenhuma regressão.

- [ ] **Step 8: Commit**

```bash
git add apps/hedge/ templates/hedge/
git commit -m "feat: views de hedge com cenários e proteção (TDD)"
```

---

## Verificação Final

Após todas as tasks concluídas:

- [ ] Rodar suite completa uma última vez:

```bash
python manage.py test tests apps.contas apps.vendas apps.posicao apps.hedge
```

Esperado: todos os testes passando.

- [ ] Subir o servidor e testar manualmente o fluxo completo:

```bash
python manage.py runserver
```

Testar na ordem:
1. `http://localhost:8000/` — tela de login, digitar email
2. Verificar email no console do terminal
3. Usar o link para autenticar
4. Criar uma safra em `http://localhost:8000/safra/nova/`
5. Ver o painel em `http://localhost:8000/painel/`
6. Adicionar uma venda em `http://localhost:8000/vendas/nova/<id>/`
7. Ver os cenários em `http://localhost:8000/hedge/<id>/cenarios/`
