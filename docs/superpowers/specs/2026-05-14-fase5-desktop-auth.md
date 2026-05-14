# HedgeFácil — Fase 5: Desktop UX + Auth Padrão Django

**Data:** 2026-05-14
**Objetivo:** Substituir magic link por autenticação username/password e adaptar o layout para desktop responsivo.

---

## 1. Auth — Login e Registro Padrão

### Motivação
O sistema usa `django-sesame` (magic link por email). Para uso local/desktop, autenticação clássica username+password é mais simples e imediata.

### Views (`apps/contas/views.py`)

**`login_view(request)`**
- Substituir `solicitar_login` inteiramente
- GET: renderiza `contas/login.html` com `AuthenticationForm`
- POST válido: `auth.login()` + redirect para `posicao:painel`
- POST inválido: re-renderiza com erros

**`register_view(request)`** — nova view
- GET: renderiza `contas/registro.html` com `RegisterForm`
- POST válido: cria `Produtor`, faz login automático, redirect para `safra:nova`
- POST inválido: re-renderiza com erros

**`logout_view`** — sem alteração

### Form (`apps/contas/forms.py`) — novo arquivo
```python
class RegisterForm(forms.ModelForm):
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)
    # valida password1 == password2
    # Meta: model=Produtor, fields=[username, email]
```

### URLs (`apps/contas/urls.py`)
```
""            → login_view      (name: login)
"registro/"   → register_view   (name: registro)
"logout/"     → logout_view     (name: logout)
```
Remove rota `email-enviado/`.

### Settings (`core/settings.py`)
- Remover `sesame.backends.ModelBackend` de `AUTHENTICATION_BACKENDS`
- Manter apenas `django.contrib.auth.backends.ModelBackend`
- Adicionar `LOGIN_URL = "contas:login"`
- Remover `SESAME_MAX_AGE`

### Templates
**`contas/login.html`** — reescrita completa, standalone (sem sidebar/header), card centralizado.
**`contas/registro.html`** — novo, mesmo estilo do login.

### Testes (8 novos em `apps/contas/tests.py`)
- `test_login_get_200`
- `test_login_post_valido_autentica`
- `test_login_post_valido_redireciona_para_painel`
- `test_login_post_invalido_retorna_200`
- `test_registro_get_200`
- `test_registro_post_valido_cria_produtor`
- `test_registro_post_valido_faz_login_automatico`
- `test_registro_post_invalido_retorna_200`

Manter os 3 testes de logout existentes.

---

## 2. Layout Desktop Responsivo

### Problema atual
`base.html` tem `max-width: 430px` no `body` — comportamento de app mobile mesmo em desktop.

### Solução
Layout de duas colunas no desktop (≥ 768px / breakpoint `md`):
- **Sidebar fixa** (240px) à esquerda com logo, navegação, usuário + logout
- **Área principal** (`ml-60`) com conteúdo centralizado (`max-w-3xl mx-auto`)

No mobile (< 768px): sidebar oculta, volta ao layout atual com header + bottom bar.

### `templates/base.html` — reescrita
```
<body class="bg-slate-50">
  <!-- sidebar: hidden no mobile, flex no md+ -->
  {% include "partials/_sidebar.html" %}

  <!-- header mobile: visível só no mobile -->
  {% include "partials/_header.html" %}

  <div class="md:ml-60">
    <main class="px-5 py-6 max-w-3xl mx-auto pb-24 md:pb-6">
      {% block conteudo %}{% endblock %}
    </main>
  </div>

  <!-- bottom bar: visível só no mobile -->
  {% include "partials/_bottom_bar.html" %}
</body>
```

### `templates/partials/_sidebar.html` — novo
```
<aside class="hidden md:flex flex-col fixed inset-y-0 left-0 w-60 bg-green-800 text-white z-10">
  <!-- Logo -->
  <div class="px-6 py-5 border-b border-green-700">
    <span class="font-display font-bold text-xl">HedgeFácil</span>
  </div>
  <!-- Nav links -->
  <nav class="flex-1 px-3 py-4 space-y-1">
    <a href="{% url 'posicao:painel' %}" class="nav-link">📊 Painel</a>
    <a href="{% url 'safra:lista' %}" class="nav-link">🌾 Safras</a>
    {% if safra %}
    <a href="{% url 'vendas:lista' safra.id %}" class="nav-link">📋 Vendas</a>
    <a href="{% url 'hedge:cenarios' safra.id %}" class="nav-link">🌱 Hedge</a>
    {% endif %}
  </nav>
  <!-- Usuário + logout -->
  {% if user.is_authenticated %}
  <div class="px-6 py-4 border-t border-green-700">
    <p class="text-xs text-green-300 mb-2">{{ user.username }}</p>
    <form method="post" action="{% url 'contas:logout' %}">
      {% csrf_token %}
      <button class="text-sm text-green-200 hover:text-white">Sair</button>
    </form>
  </div>
  {% endif %}
</aside>
```

### `templates/partials/_header.html` — atualizar
Adicionar `class="md:hidden"` ao `<header>` (visível apenas no mobile).

### `templates/partials/_bottom_bar.html` — atualizar
Adicionar `class="md:hidden"` ao `<nav>` (visível apenas no mobile).

### Templates de auth — standalone
`contas/login.html` e `contas/registro.html` não estendem `base.html` — são páginas independentes sem sidebar nem header (layout de login centrado na tela).

---

## Arquivos modificados/criados

| Arquivo | Ação |
|---------|------|
| `apps/contas/views.py` | Substituir `solicitar_login` por `login_view`, adicionar `register_view` |
| `apps/contas/forms.py` | Criar `RegisterForm` |
| `apps/contas/urls.py` | Atualizar rotas |
| `apps/contas/tests.py` | Adicionar 8 testes |
| `core/settings.py` | Remover sesame backend, adicionar `LOGIN_URL` |
| `templates/contas/login.html` | Reescrever (standalone) |
| `templates/contas/registro.html` | Criar (standalone) |
| `templates/contas/email_enviado.html` | Deletar |
| `templates/base.html` | Layout responsivo sidebar+main |
| `templates/partials/_sidebar.html` | Criar |
| `templates/partials/_header.html` | Adicionar `md:hidden` |
| `templates/partials/_bottom_bar.html` | Adicionar `md:hidden` |

## Contagem de testes

| Task | Novos | Total |
|------|-------|-------|
| Baseline (Fase 4) | — | 125 |
| Task 1 (Auth) | 8 | 133 |
| Task 2 (Layout) | 0 | 133 |
