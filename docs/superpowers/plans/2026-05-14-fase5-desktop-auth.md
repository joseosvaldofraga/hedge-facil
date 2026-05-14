# HedgeFácil — Fase 5: Desktop UX + Auth Padrão Django

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Substituir magic link por login username/password e dar ao sistema um layout desktop responsivo com sidebar.

**Architecture:** Duas tasks independentes — Task 1 troca o sistema de auth (sesame → Django padrão), Task 2 adiciona sidebar fixa no desktop e remove a restrição de 430px. Nenhuma mudança nos models, services ou lógica de negócio.

**Tech Stack:** Django 6, Tailwind CDN, HTMX 2.0, Produtor extends AbstractUser (username/password já funciona nativamente).

---

## Arquivos

| Arquivo | Ação |
|---------|------|
| `apps/contas/forms.py` | Criar — `RegisterForm` |
| `apps/contas/views.py` | Substituir `solicitar_login` por `login_view`, adicionar `register_view` |
| `apps/contas/urls.py` | Trocar rota `""` e `email-enviado/`, adicionar `registro/` |
| `apps/contas/tests.py` | Remover `LoginMagicoTestCase` (6 testes), adicionar `LoginViewTestCase` (4) e `RegisterViewTestCase` (4) |
| `core/settings.py` | Remover `sesame.backends.ModelBackend` e `SESAME_MAX_AGE`, corrigir `LOGIN_URL` |
| `templates/contas/login.html` | Reescrever — standalone, card centrado |
| `templates/contas/registro.html` | Criar — standalone, card centrado |
| `templates/contas/email_enviado.html` | Deletar |
| `templates/base.html` | Reescrever — layout responsivo com sidebar slot |
| `templates/partials/_sidebar.html` | Criar — nav desktop |
| `templates/partials/_header.html` | Adicionar `md:hidden` |
| `templates/partials/_bottom_bar.html` | Atualizar — `md:hidden` + link Safras |

## Contagem de testes

| Task | Mudança | Total |
|------|---------|-------|
| Baseline (Fase 4) | — | 125 |
| Task 1 (Auth) | -6 LoginMagico + 8 novos | 127 |
| Task 2 (Layout) | 0 | 127 |

---

## Task 1: Auth Padrão Django (login + registro)

**Files:**
- Create: `apps/contas/forms.py`
- Modify: `apps/contas/views.py`
- Modify: `apps/contas/urls.py`
- Modify: `apps/contas/tests.py`
- Modify: `core/settings.py`
- Rewrite: `templates/contas/login.html`
- Create: `templates/contas/registro.html`
- Delete: `templates/contas/email_enviado.html`

### RED: substituir LoginMagicoTestCase e adicionar RegisterViewTestCase

- [ ] **Step 1: Escrever os testes que vão falhar**

Abrir `apps/contas/tests.py`. Remover a classe `LoginMagicoTestCase` inteira (6 testes) e substituir por `LoginViewTestCase`. Adicionar `RegisterViewTestCase` após `LogoutViewTestCase`.

```python
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from apps.contas.models import Produtor


class LoginViewTestCase(TestCase):
    def setUp(self):
        self.produtor = Produtor.objects.create_user(
            username="fazendeiro", email="f@test.com", password="senha123"
        )

    def test_login_get_200(self):
        response = self.client.get(reverse("contas:login"))
        self.assertEqual(response.status_code, 200)

    def test_login_post_valido_autentica(self):
        self.client.post(reverse("contas:login"), {
            "username": "fazendeiro", "password": "senha123"
        })
        response = self.client.get(reverse("posicao:painel"))
        self.assertEqual(response.wsgi_request.user.username, "fazendeiro")

    def test_login_post_valido_redireciona_para_painel(self):
        response = self.client.post(reverse("contas:login"), {
            "username": "fazendeiro", "password": "senha123"
        })
        self.assertRedirects(response, reverse("posicao:painel"),
                             fetch_redirect_response=False)

    def test_login_post_invalido_retorna_200(self):
        response = self.client.post(reverse("contas:login"), {
            "username": "fazendeiro", "password": "errada"
        })
        self.assertEqual(response.status_code, 200)


class RegisterViewTestCase(TestCase):
    def _dados_validos(self):
        return {
            "username": "novoprodutor",
            "email": "novo@test.com",
            "password1": "senhaSegura99",
            "password2": "senhaSegura99",
        }

    def test_registro_get_200(self):
        response = self.client.get(reverse("contas:registro"))
        self.assertEqual(response.status_code, 200)

    def test_registro_post_valido_cria_produtor(self):
        self.client.post(reverse("contas:registro"), self._dados_validos())
        self.assertTrue(Produtor.objects.filter(username="novoprodutor").exists())

    def test_registro_post_valido_faz_login_automatico(self):
        response = self.client.post(reverse("contas:registro"), self._dados_validos())
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_registro_post_invalido_retorna_200(self):
        response = self.client.post(reverse("contas:registro"), {
            "username": "x", "email": "x@test.com",
            "password1": "abc", "password2": "diferente",
        })
        self.assertEqual(response.status_code, 200)


class LogoutViewTestCase(TestCase):
    def setUp(self):
        self.produtor = Produtor.objects.create_user(
            username="ze_logout", email="ze_logout@test.com", password="senha123"
        )
        self.client.force_login(self.produtor)

    def test_logout_post_desloga_usuario(self):
        response = self.client.post(reverse("contas:logout"))
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_logout_post_redireciona_para_login(self):
        response = self.client.post(reverse("contas:logout"))
        self.assertRedirects(response, reverse("contas:login"))

    def test_logout_get_nao_permitido(self):
        response = self.client.get(reverse("contas:logout"))
        self.assertEqual(response.status_code, 405)
```

- [ ] **Step 2: Rodar os testes — esperar falhas**

```bash
cd /media/fragatec/SSD/projetos/web/hedgefacil
.venv/bin/python manage.py test apps.contas --verbosity=0 2>&1 | tail -10
```

Esperado: erros de `NoReverseMatch` para `contas:registro` e falhas nos testes de login.

### GREEN: implementar auth padrão

- [ ] **Step 3: Criar `apps/contas/forms.py`**

```python
from django import forms
from .models import Produtor


class RegisterForm(forms.Form):
    username = forms.CharField(max_length=150, label="Usuário")
    email = forms.EmailField(label="Email")
    password1 = forms.CharField(widget=forms.PasswordInput, label="Senha")
    password2 = forms.CharField(widget=forms.PasswordInput, label="Confirmar senha")

    def clean_username(self):
        username = self.cleaned_data["username"]
        if Produtor.objects.filter(username=username).exists():
            raise forms.ValidationError("Este nome de usuário já está em uso.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password1")
        p2 = cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("As senhas não coincidem.")
        return cleaned_data

    def save(self):
        return Produtor.objects.create_user(
            username=self.cleaned_data["username"],
            email=self.cleaned_data["email"],
            password=self.cleaned_data["password1"],
        )
```

- [ ] **Step 4: Reescrever `apps/contas/views.py`**

```python
from django.shortcuts import render, redirect
from django.contrib import auth
from django.contrib.auth.forms import AuthenticationForm
from django.views.decorators.http import require_POST
from .forms import RegisterForm


def login_view(request):
    form = AuthenticationForm(data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        auth.login(request, form.get_user())
        return redirect("posicao:painel")
    return render(request, "contas/login.html", {"form": form})


def register_view(request):
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        produtor = form.save()
        auth.login(request, produtor)
        return redirect("safra:nova")
    return render(request, "contas/registro.html", {"form": form})


@require_POST
def logout_view(request):
    auth.logout(request)
    return redirect("contas:login")
```

- [ ] **Step 5: Atualizar `apps/contas/urls.py`**

```python
from django.urls import path
from . import views

app_name = "contas"

urlpatterns = [
    path("", views.login_view, name="login"),
    path("registro/", views.register_view, name="registro"),
    path("logout/", views.logout_view, name="logout"),
]
```

- [ ] **Step 6: Atualizar `core/settings.py`**

Remover as linhas:
```python
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "sesame.backends.ModelBackend",
]

SESAME_MAX_AGE = 60 * 60 * 24
```

Substituir por:
```python
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]
```

E trocar:
```python
LOGIN_URL = "/"
LOGIN_REDIRECT_URL = "/painel/"
```

Por:
```python
LOGIN_URL = "contas:login"
LOGIN_REDIRECT_URL = "/painel/"
```

- [ ] **Step 7: Reescrever `templates/contas/login.html`**

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Entrar — HedgeFácil</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link href="https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@400;500&display=swap" rel="stylesheet">
  <style>body { font-family: 'DM Sans', sans-serif; } .font-display { font-family: 'Syne', sans-serif; }</style>
</head>
<body class="bg-slate-50 min-h-screen flex items-center justify-center">
  <div class="w-full max-w-sm px-6">
    <div class="mb-8 text-center">
      <h1 class="font-display text-3xl font-bold text-green-800">HedgeFácil</h1>
      <p class="text-slate-500 text-sm mt-1">Gestão de hedge para produtores</p>
    </div>
    <div class="bg-white rounded-2xl shadow-sm border border-slate-200 p-8">
      <h2 class="font-display text-xl font-bold text-slate-800 mb-6">Entrar</h2>
      <form method="post">
        {% csrf_token %}
        {% if form.non_field_errors %}
          <div class="bg-red-50 border border-red-200 rounded-lg px-4 py-3 mb-4">
            <p class="text-red-700 text-sm">{{ form.non_field_errors.0 }}</p>
          </div>
        {% endif %}
        <div class="mb-4">
          <label class="block text-sm font-medium text-slate-700 mb-1">Usuário</label>
          <input type="text" name="username" value="{{ form.username.value|default:'' }}"
            class="w-full border border-slate-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-green-500">
          {% if form.username.errors %}<p class="text-red-600 text-xs mt-1">{{ form.username.errors.0 }}</p>{% endif %}
        </div>
        <div class="mb-6">
          <label class="block text-sm font-medium text-slate-700 mb-1">Senha</label>
          <input type="password" name="password"
            class="w-full border border-slate-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-green-500">
          {% if form.password.errors %}<p class="text-red-600 text-xs mt-1">{{ form.password.errors.0 }}</p>{% endif %}
        </div>
        <button type="submit"
          class="w-full bg-green-700 hover:bg-green-800 text-white font-semibold py-2.5 rounded-lg text-sm transition-colors">
          Entrar
        </button>
      </form>
      <p class="text-center text-sm text-slate-500 mt-5">
        Não tem conta?
        <a href="{% url 'contas:registro' %}" class="text-green-700 font-medium hover:underline">Criar conta</a>
      </p>
    </div>
  </div>
</body>
</html>
```

- [ ] **Step 8: Criar `templates/contas/registro.html`**

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Criar conta — HedgeFácil</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link href="https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@400;500&display=swap" rel="stylesheet">
  <style>body { font-family: 'DM Sans', sans-serif; } .font-display { font-family: 'Syne', sans-serif; }</style>
</head>
<body class="bg-slate-50 min-h-screen flex items-center justify-center py-8">
  <div class="w-full max-w-sm px-6">
    <div class="mb-8 text-center">
      <h1 class="font-display text-3xl font-bold text-green-800">HedgeFácil</h1>
      <p class="text-slate-500 text-sm mt-1">Gestão de hedge para produtores</p>
    </div>
    <div class="bg-white rounded-2xl shadow-sm border border-slate-200 p-8">
      <h2 class="font-display text-xl font-bold text-slate-800 mb-6">Criar conta</h2>
      <form method="post">
        {% csrf_token %}
        {% if form.non_field_errors %}
          <div class="bg-red-50 border border-red-200 rounded-lg px-4 py-3 mb-4">
            <p class="text-red-700 text-sm">{{ form.non_field_errors.0 }}</p>
          </div>
        {% endif %}
        <div class="mb-4">
          <label class="block text-sm font-medium text-slate-700 mb-1">Usuário</label>
          <input type="text" name="username" value="{{ form.username.value|default:'' }}"
            class="w-full border border-slate-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-green-500">
          {% if form.username.errors %}<p class="text-red-600 text-xs mt-1">{{ form.username.errors.0 }}</p>{% endif %}
        </div>
        <div class="mb-4">
          <label class="block text-sm font-medium text-slate-700 mb-1">Email</label>
          <input type="email" name="email" value="{{ form.email.value|default:'' }}"
            class="w-full border border-slate-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-green-500">
          {% if form.email.errors %}<p class="text-red-600 text-xs mt-1">{{ form.email.errors.0 }}</p>{% endif %}
        </div>
        <div class="mb-4">
          <label class="block text-sm font-medium text-slate-700 mb-1">Senha</label>
          <input type="password" name="password1"
            class="w-full border border-slate-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-green-500">
          {% if form.password1.errors %}<p class="text-red-600 text-xs mt-1">{{ form.password1.errors.0 }}</p>{% endif %}
        </div>
        <div class="mb-6">
          <label class="block text-sm font-medium text-slate-700 mb-1">Confirmar senha</label>
          <input type="password" name="password2"
            class="w-full border border-slate-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-green-500">
          {% if form.password2.errors %}<p class="text-red-600 text-xs mt-1">{{ form.password2.errors.0 }}</p>{% endif %}
        </div>
        <button type="submit"
          class="w-full bg-green-700 hover:bg-green-800 text-white font-semibold py-2.5 rounded-lg text-sm transition-colors">
          Criar conta
        </button>
      </form>
      <p class="text-center text-sm text-slate-500 mt-5">
        Já tem conta?
        <a href="{% url 'contas:login' %}" class="text-green-700 font-medium hover:underline">Entrar</a>
      </p>
    </div>
  </div>
</body>
</html>
```

- [ ] **Step 9: Deletar `templates/contas/email_enviado.html`**

```bash
rm /media/fragatec/SSD/projetos/web/hedgefacil/templates/contas/email_enviado.html
```

- [ ] **Step 10: Verificar e corrigir testes**

```bash
cd /media/fragatec/SSD/projetos/web/hedgefacil
.venv/bin/python manage.py test apps.contas --verbosity=0 2>&1 | tail -5
```

Esperado: `Ran 11 tests ... OK`

- [ ] **Step 11: Rodar suite completa**

```bash
.venv/bin/python manage.py test --verbosity=0 2>&1 | tail -5
```

Esperado: `Ran 127 tests ... OK`

- [ ] **Step 12: Commit**

```bash
cd /media/fragatec/SSD/projetos/web/hedgefacil
git add apps/contas/forms.py apps/contas/views.py apps/contas/urls.py apps/contas/tests.py
git add core/settings.py
git add templates/contas/login.html templates/contas/registro.html
git rm templates/contas/email_enviado.html
git commit -m "task 1: auth padrao django — login/registro username+password, remove sesame"
```

---

## Task 2: Layout Desktop Responsivo

**Files:**
- Rewrite: `templates/base.html`
- Create: `templates/partials/_sidebar.html`
- Modify: `templates/partials/_header.html`
- Modify: `templates/partials/_bottom_bar.html`

Sem testes novos — mudanças de template puro.

- [ ] **Step 1: Reescrever `templates/base.html`**

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% block titulo %}HedgeFácil{% endblock %}</title>
  <script src="https://unpkg.com/htmx.org@2.0.0"></script>
  <script src="https://cdn.tailwindcss.com"></script>
  <link href="https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=DM+Sans:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    body { font-family: 'DM Sans', sans-serif; }
    .font-display { font-family: 'Syne', sans-serif; }
    .htmx-indicator { display: none; }
    .htmx-request .htmx-indicator { display: inline; }
    .htmx-request .htmx-indicator-hide { display: none; }
  </style>
</head>
<body class="bg-slate-50 text-slate-900">
  {% include "partials/_sidebar.html" %}
  {% include "partials/_header.html" %}
  <div class="md:ml-60">
    <main class="px-5 py-4 max-w-3xl mx-auto pb-24 md:pb-8">
      {% block conteudo %}{% endblock %}
    </main>
  </div>
  {% include "partials/_bottom_bar.html" %}
</body>
</html>
```

- [ ] **Step 2: Criar `templates/partials/_sidebar.html`**

```html
{% if user.is_authenticated %}
<aside class="hidden md:flex flex-col fixed inset-y-0 left-0 w-60 bg-green-800 text-white z-10">
  <div class="px-6 py-5 border-b border-green-700">
    <span class="font-display font-bold text-xl">HedgeFácil</span>
  </div>
  <nav class="flex-1 px-3 py-4 space-y-1">
    <a href="{% url 'posicao:painel' %}"
       class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-green-100 hover:bg-green-700 hover:text-white transition-colors">
      <span>📊</span> Painel
    </a>
    <a href="{% url 'safra:lista' %}"
       class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-green-100 hover:bg-green-700 hover:text-white transition-colors">
      <span>🌾</span> Safras
    </a>
    {% if safra %}
    <a href="{% url 'vendas:lista' safra.id %}"
       class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-green-100 hover:bg-green-700 hover:text-white transition-colors">
      <span>📋</span> Vendas
    </a>
    <a href="{% url 'hedge:cenarios' safra.id %}"
       class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-green-100 hover:bg-green-700 hover:text-white transition-colors">
      <span>🌱</span> Hedge
    </a>
    {% endif %}
  </nav>
  <div class="px-6 py-4 border-t border-green-700">
    <p class="text-xs text-green-300 mb-2">{{ user.username }}</p>
    <form method="post" action="{% url 'contas:logout' %}">
      {% csrf_token %}
      <button type="submit"
        class="text-sm text-green-200 hover:text-white bg-transparent border-0 cursor-pointer transition-colors">
        Sair
      </button>
    </form>
  </div>
</aside>
{% endif %}
```

- [ ] **Step 3: Atualizar `templates/partials/_header.html`**

```html
{% if user.is_authenticated %}
<header class="md:hidden bg-green-800 text-white px-5 py-3 flex justify-between items-center">
  <span class="font-display font-bold text-lg">HedgeFácil</span>
  <form method="post" action="{% url 'contas:logout' %}">
    {% csrf_token %}
    <button type="submit" class="text-sm text-green-200 bg-transparent border-0 cursor-pointer">Sair</button>
  </form>
</header>
{% endif %}
```

- [ ] **Step 4: Atualizar `templates/partials/_bottom_bar.html`**

```html
{% if user.is_authenticated %}
<nav class="md:hidden fixed bottom-0 left-0 right-0 bg-white border-t border-slate-200 flex justify-around py-3">
  <a href="{% url 'posicao:painel' %}" class="flex flex-col items-center text-xs text-slate-600">
    <span>📊</span>Posição
  </a>
  <a href="{% url 'safra:lista' %}" class="flex flex-col items-center text-xs text-slate-600">
    <span>🌾</span>Safras
  </a>
  <a href="{% url 'hedge:redirect' %}" class="flex flex-col items-center text-xs text-slate-600">
    <span>🌱</span>Hedge
  </a>
</nav>
{% endif %}
```

- [ ] **Step 5: Rodar suite completa**

```bash
cd /media/fragatec/SSD/projetos/web/hedgefacil
.venv/bin/python manage.py test --verbosity=0 2>&1 | tail -5
```

Esperado: `Ran 127 tests ... OK`

- [ ] **Step 6: Commit**

```bash
cd /media/fragatec/SSD/projetos/web/hedgefacil
git add templates/base.html templates/partials/_sidebar.html
git add templates/partials/_header.html templates/partials/_bottom_bar.html
git commit -m "task 2: layout desktop responsivo com sidebar, remove max-width 430px"
```
