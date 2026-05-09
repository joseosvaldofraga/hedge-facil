# HedgeFácil — Especificação Técnica

> **Sistema de controle comercial da safra do produtor rural com simulação de hedge integrada.**
> Stack: Django 5 + HTMX + PostgreSQL + Tailwind (via CDN) — zero build, zero SPA, server-side rendering.

---

## 1. Princípios de Arquitetura

Antes de qualquer linha de código, internalizar:

**Django sem firulas.** Templates Django renderizam HTML. HTMX faz interatividade. PostgreSQL persiste. Nada de DRF, nada de React, nada de Celery na fase 1. Cada dependência adicional é dívida.

**Mobile-first de verdade.** Produtor usa no celular Android intermediário, em 4G instável, sob sol forte. Página tem que abrir em menos de 2 segundos no 4G e ser legível com a tela na luz do dia. Tudo é desenhado pra essa realidade primeiro.

**Linguagem rural em todo lugar.** Modelo se chama `Venda`, não `Transaction`. Campo se chama `sacas`, não `quantity`. Status é `Vendido`, `A vender`, `Travado` — não `SOLD`, `PENDING`, `LOCKED`. O código reflete o domínio.

**Render server-side, sempre.** HTMX troca pedaços de HTML, não JSON. Cada interação retorna fragmento renderizado pelo Django. Isso elimina toda complexidade de estado no front.

**Banco como fonte de verdade única.** Sem cache esoterico, sem estado em sessão. PostgreSQL responde. Quando virar gargalo (não vai virar nos primeiros 100 usuários), aí pensa em cache.

**Testes onde dói.** Não testar tudo. Testar cálculos financeiros (preço médio ponderado, projeção de cenários, simulação de hedge). Esses não podem errar — produtor toma decisão em cima.

---

## 2. Stack Confirmada

| Camada | Tecnologia | Versão | Por quê |
|---|---|---|---|
| Linguagem | Python | 3.12+ | Estável, type hints maduros |
| Framework | Django | 5.0+ | Server-side rendering, admin pronto, ORM excelente |
| Banco | PostgreSQL | 16+ | Decimal preciso, transações, JSON quando precisar |
| Front interativo | HTMX | 2.0 (CDN) | Interatividade sem JS complexo |
| CSS | Tailwind | CDN inicial | Sem build, classes utilitárias |
| Forms | django-crispy-forms + crispy-tailwind | última | Forms bonitas com pouco código |
| Decimais | `decimal.Decimal` em todo lugar | nativo | Float em dinheiro é proibido |
| Deploy | Railway ou Fly.io | — | Postgres gerenciado, deploy git push |
| Auth | Django auth nativo + login mágico por email | nativo + django-sesame | Produtor não cria senha |

**Dependências (pip):**
```
django>=5.0
psycopg[binary]>=3.1
django-htmx>=1.17
django-crispy-forms>=2.1
crispy-tailwind>=1.0
django-sesame>=3.2
python-decouple>=3.8
whitenoise>=6.6
gunicorn>=21.2
```

Nada além disso na fase 1. Cada nova dependência exige justificativa por escrito no PR.

---

## 3. Estrutura de Pastas

```
hedgefacil/
├── manage.py
├── requirements.txt
├── .env                       # SECRET_KEY, DATABASE_URL, EMAIL_*
├── .gitignore
├── README.md
├── CLAUDE.md                  # este arquivo
│
├── core/                      # configuração do projeto Django
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── apps/
│   ├── contas/                # autenticação, perfil do produtor
│   │   ├── models.py          # Produtor (extends User)
│   │   ├── views.py           # login mágico, perfil
│   │   ├── urls.py
│   │   └── templates/contas/
│   │
│   ├── safra/                 # safra atual e produção
│   │   ├── models.py          # Safra, Cultura
│   │   ├── views.py
│   │   ├── forms.py
│   │   ├── urls.py
│   │   └── templates/safra/
│   │
│   ├── vendas/                # vendas realizadas (termo, CPR, balcão, B3)
│   │   ├── models.py          # Venda, TipoVenda, Contraparte
│   │   ├── views.py           # CRUD + listagem
│   │   ├── forms.py
│   │   ├── urls.py
│   │   └── templates/vendas/
│   │
│   ├── posicao/               # painel de posição da safra
│   │   ├── views.py           # cálculos agregados
│   │   ├── services.py        # lógica de cálculo (preço médio, % vendido)
│   │   ├── urls.py
│   │   └── templates/posicao/
│   │
│   └── hedge/                 # simulador de cenários e proteção
│       ├── models.py          # Cenario, SimulacaoHedge
│       ├── services.py        # cálculo de cenários e instrumentos
│       ├── views.py
│       ├── urls.py
│       └── templates/hedge/
│
├── templates/                 # templates globais
│   ├── base.html
│   ├── partials/              # fragmentos HTMX
│   │   ├── _header.html
│   │   ├── _bottom_bar.html
│   │   └── _venda_item.html
│   └── components/            # componentes reusáveis
│       ├── card.html
│       ├── botao.html
│       └── numero_grande.html
│
├── static/
│   ├── css/                   # depois migrar de CDN pra arquivo
│   └── img/
│
└── tests/
    ├── test_calculos.py       # crítico: preço médio, cenários
    └── test_modelos.py
```

**Regra de ouro:** cada app é independente, expõe URLs e usa serviços de outros apps via importação explícita. Sem circular imports.

---

## 4. Modelos de Dados

Esquema mínimo da fase 1. Decimal em todo dinheiro, nunca Float.

### `apps/contas/models.py`

```python
from django.contrib.auth.models import AbstractUser
from django.db import models

class Produtor(AbstractUser):
    """Usuário do sistema = produtor rural."""
    whatsapp = models.CharField(max_length=20, blank=True)
    cidade = models.CharField(max_length=100, blank=True)
    estado = models.CharField(max_length=2, blank=True)
    aceitou_termos_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Produtor"
        verbose_name_plural = "Produtores"
```

Configurar em settings.py: `AUTH_USER_MODEL = "contas.Produtor"`.

### `apps/safra/models.py`

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
    """Uma safra de uma cultura específica de um produtor."""
    produtor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="safras")
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

### `apps/vendas/models.py`

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
    safra = models.ForeignKey("safra.Safra", on_delete=models.CASCADE, related_name="vendas")
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

### `apps/hedge/models.py`

Modelar quando virar persistente. Na fase inicial, simulação é stateless — calcula e mostra, não salva.

---

## 5. Cálculos Críticos (`services.py`)

A regra: **toda lógica financeira sai de `views.py` e fica em `services.py` testável**.

### `apps/posicao/services.py`

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
    lucro_travado_parcial: Decimal  # receita_travada - (sacas_vendidas * custo_por_saca)


def calcular_posicao(safra: Safra) -> PosicaoSafra:
    vendas = safra.vendas.all()
    sacas_vendidas = sum((v.sacas for v in vendas), Decimal("0"))
    receita_travada = sum((v.receita for v in vendas), Decimal("0"))

    if sacas_vendidas > 0:
        preco_medio = receita_travada / sacas_vendidas
    else:
        preco_medio = Decimal("0")

    sacas_a_vender = safra.producao_estimada_sacas - sacas_vendidas
    percentual = (sacas_vendidas / safra.producao_estimada_sacas * 100) if safra.producao_estimada_sacas > 0 else Decimal("0")

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

### `apps/hedge/services.py`

```python
from decimal import Decimal
from dataclasses import dataclass

@dataclass
class CenarioPreco:
    nome: str  # "Queda 20%", "Estável", "Alta 15%"
    variacao_percentual: Decimal  # -20, 0, 15
    preco_projetado: Decimal
    receita_no_saldo: Decimal  # sacas_a_vender * preco_projetado
    impacto_vs_atual: Decimal  # diferença em R$ vs cenário estável


def simular_cenarios(
    sacas_a_vender: Decimal,
    preco_atual: Decimal,
    variacoes: list[Decimal] = None
) -> list[CenarioPreco]:
    """Calcula receita projetada nos cenários de preço."""
    if variacoes is None:
        variacoes = [Decimal("-20"), Decimal("0"), Decimal("15")]

    nomes = {
        Decimal("-20"): "Preço cai 20%",
        Decimal("0"): "Preço fica igual",
        Decimal("15"): "Preço sobe 15%",
    }

    receita_estavel = sacas_a_vender * preco_atual
    cenarios = []

    for var in variacoes:
        preco = preco_atual * (Decimal("1") + var / Decimal("100"))
        receita = sacas_a_vender * preco
        impacto = receita - receita_estavel

        cenarios.append(CenarioPreco(
            nome=nomes.get(var, f"Variação {var}%"),
            variacao_percentual=var,
            preco_projetado=preco.quantize(Decimal("0.01")),
            receita_no_saldo=receita.quantize(Decimal("0.01")),
            impacto_vs_atual=impacto.quantize(Decimal("0.01")),
        ))

    return cenarios
```

**Testar tudo isso.** O arquivo `tests/test_calculos.py` é prioridade absoluta. Cálculo errado de preço médio = produtor toma decisão errada = projeto morre.

---

## 6. Padrão HTMX

Todo padrão HTMX nesse projeto segue:

**1. View detecta HTMX e retorna fragmento.** Usar `django-htmx`:

```python
def adicionar_venda(request, safra_id):
    safra = get_object_or_404(Safra, id=safra_id, produtor=request.user)
    if request.method == "POST":
        form = VendaForm(request.POST)
        if form.is_valid():
            venda = form.save(commit=False)
            venda.safra = safra
            venda.save()
            if request.htmx:
                return render(request, "vendas/_lista.html", {"vendas": safra.vendas.all()})
            return redirect("posicao:detalhe", safra_id=safra.id)
    else:
        form = VendaForm()
    return render(request, "vendas/_form.html", {"form": form, "safra": safra})
```

**2. Templates de fragmento têm prefixo `_`.** `_form.html`, `_lista.html`, `_card.html`. Convenção clara.

**3. Triggers padronizados.** Após salvar venda, dispara evento `venda:salva` que atualiza painel de posição:

```html
<form hx-post="{% url 'vendas:adicionar' safra.id %}"
      hx-target="#lista-vendas"
      hx-swap="outerHTML"
      hx-trigger="submit"
      hx-on::after-request="htmx.trigger('#painel-posicao', 'recarregar')">
```

**4. Loading states sempre.** Botão tem `hx-indicator` mostrando spinner. Conexão em campo é ruim, feedback visual é obrigatório.

```html
<button class="btn-primario" type="submit">
  <span class="htmx-indicator-hide">Salvar venda</span>
  <span class="htmx-indicator">Salvando...</span>
</button>
```

---

## 7. Templates Mobile-First

**`templates/base.html`** define o esqueleto. Largura máxima 430px no desktop (preview de mobile), 100% no celular real:

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

**Princípios visuais herdados do protótipo:**
- Verde escuro (#1a7a4a) como primário
- Vermelho (#c0392b) só pra alerta de perda
- Verde claro pra ganho/proteção
- Fonte display Syne pros números grandes (impacto)
- Fonte texto DM Sans pra legibilidade
- Botões grandes (mín 48px de altura) — dedo molhado de produtor não acerta botão pequeno
- Tudo em R$ formatado com separador brasileiro (12.000 não 12,000)

---

## 8. Autenticação por Link Mágico

Produtor não cria senha. Fluxo:

1. Produtor digita WhatsApp ou email → recebe link
2. Link autentica e cria sessão de 30 dias

Usar `django-sesame`:

```python
# settings.py
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "sesame.backends.ModelBackend",
]
SESAME_MAX_AGE = 60 * 60 * 24  # link válido por 24h

# views.py
from sesame.utils import get_query_string

def solicitar_login(request):
    if request.method == "POST":
        email = request.POST.get("email")
        produtor, _ = Produtor.objects.get_or_create(email=email, defaults={"username": email})
        link = request.build_absolute_uri("/painel/") + get_query_string(produtor)
        # enviar por email (fase 1) ou WhatsApp via API (fase 2)
        send_mail("Acesso HedgeFácil", f"Acesse: {link}", "no-reply@hedgefacil.com.br", [email])
        return render(request, "contas/email_enviado.html")
    return render(request, "contas/login.html")
```

---

## 9. URLs e Fluxo Principal

```python
# core/urls.py
from django.urls import path, include

urlpatterns = [
    path("", include("apps.contas.urls")),                # / → login
    path("painel/", include("apps.posicao.urls")),        # /painel/ → posição da safra atual
    path("safra/", include("apps.safra.urls")),           # /safra/nova/, /safra/<id>/
    path("vendas/", include("apps.vendas.urls")),         # /vendas/<safra_id>/, /vendas/nova/<safra_id>/
    path("hedge/", include("apps.hedge.urls")),           # /hedge/<safra_id>/cenarios/, /hedge/<safra_id>/proteger/
    path("admin/", admin.site.urls),
]
```

**Fluxo do produtor logado:**
- `/` → se não logado, login; se logado, redireciona pra `/painel/`
- `/painel/` → posição da safra ativa (se não tem safra, redireciona pra criar)
- `/safra/nova/` → form de criação de safra
- `/vendas/<safra_id>/` → lista de vendas + botão "+ Nova venda"
- `/vendas/nova/<safra_id>/` → form de nova venda (HTMX modal)
- `/hedge/<safra_id>/cenarios/` → tela 2 do protótipo, dinâmica
- `/hedge/<safra_id>/proteger/` → tela 3 do protótipo

---

## 10. Roadmap de Implementação

Cada item é uma sessão de desenvolvimento de 2-4 horas. Faz na ordem.

### Sprint 1 — Fundação (semana 1)

1. `django-admin startproject core .` + estrutura de pastas + git init
2. Configurar settings.py (DATABASE_URL, AUTH_USER_MODEL, INSTALLED_APPS)
3. Criar `Produtor` model + migrar
4. Login mágico funcionando (send_mail no console em dev)
5. Template `base.html` + header + bottom bar
6. Deploy inicial no Railway com Postgres provisionado

### Sprint 2 — Safra e Vendas (semana 2)

7. Model `Safra` + admin + form de criação
8. Tela `/safra/nova/` funcionando
9. Model `Venda` + admin
10. CRUD de Venda (criar, listar, editar, deletar) com HTMX
11. Listagem de vendas no estilo do protótipo

### Sprint 3 — Painel de Posição (semana 3)

12. `services.py` em `posicao` + testes
13. View `/painel/` renderizando hero + barra de progresso + lista (replica tela 1 do protótipo com dados reais)
14. Atualização HTMX: ao salvar venda, painel atualiza sem reload

### Sprint 4 — Hedge (semana 4)

15. `services.py` em `hedge` (cenários) + testes
16. View `/hedge/<safra_id>/cenarios/` (replica tela 2 do protótipo)
17. View `/hedge/<safra_id>/proteger/` (replica tela 3 do protótipo)
18. Botões "Quero saber como fazer" → integração WhatsApp pré-formatado

### Sprint 5 — Polimento e primeiro produtor (semana 5)

19. Cotação atual da soja: começa estática, depois fetch CEPEA
20. Exportação de PDF da posição (usar `weasyprint` ou `xhtml2pdf`)
21. Onboarding: primeiro acesso → guia rápido pra criar safra e lançar primeira venda
22. Migrar primeiro produtor real → acompanhar 30 dias

---

## 11. O que NÃO Fazer na Fase 1

Lista explícita, pra você reler quando bater a tentação:

- ❌ Não criar API REST. HTMX não precisa.
- ❌ Não usar React, Vue, Svelte. Templates Django.
- ❌ Não integrar com B3. Cotação manual ou CEPEA scraping simples.
- ❌ Não criar app mobile nativo. Web mobile resolve.
- ❌ Não fazer multi-tenant complexo. Cada produtor tem suas safras, ponto.
- ❌ Não fazer billing/Stripe. Primeiros usuários são de graça.
- ❌ Não implementar alertas em tempo real. WhatsApp manual basta.
- ❌ Não fazer dashboard de admin com gráficos. Django admin nativo serve.
- ❌ Não otimizar performance prematuramente. Postgres aguenta 100 produtores tranquilo.
- ❌ Não fazer i18n. Produto é Brasil, idioma é PT-BR, ponto.

---

## 12. Comandos Úteis

```bash
# Setup inicial
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver

# Sempre que mudar model
python manage.py makemigrations
python manage.py migrate

# Rodar testes (cálculos críticos)
python manage.py test apps.posicao.tests apps.hedge.tests

# Shell pra explorar dados
python manage.py shell
```

---

## 13. Convenções de Código

**Nomes em português** quando se refere a domínio (Safra, Venda, Produtor, sacas, preco_por_saca). **Nomes em inglês** apenas em conceitos puramente técnicos (request, response, get_object_or_404).

**Docstrings curtas** no que tem regra de negócio. Não documentar trivialidades.

**Type hints** em funções de `services.py`. Em views é opcional.

**Decimal everywhere** em dinheiro. `from decimal import Decimal` no topo de qualquer arquivo que toca preço. Float em dinheiro é bug em produção.

**Commits pequenos.** Cada sprint do roadmap = vários commits. Mensagem descritiva: "Adiciona modelo Venda + admin", não "wip".

---

## 14. Variáveis de Ambiente

`.env` na raiz, **nunca commitado**:

```env
SECRET_KEY=gera-com-django-secret
DEBUG=True
DATABASE_URL=postgres://user:pass@localhost:5432/hedgefacil
ALLOWED_HOSTS=localhost,127.0.0.1,hedgefacil.com.br
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=...
EMAIL_HOST_PASSWORD=...
DEFAULT_FROM_EMAIL=no-reply@hedgefacil.com.br
WHATSAPP_PRODUTOR_DESTINO=5519983052450
```

---

## 15. Critério de "Pronto" da Fase 1

A fase 1 termina quando **um produtor real**, sem você do lado, consegue:

1. Criar conta com email
2. Cadastrar a safra atual dele
3. Lançar 3 vendas que ele realmente fez
4. Ver o painel mostrando preço médio correto
5. Ver os cenários de queda/alta no saldo a vender
6. Clicar no WhatsApp e te chamar

Se isso funciona end-to-end, fase 1 acabou. Aí você decide o que vem depois com base no que esse produtor disse.

---

**Lembrete final:** este sistema vive ou morre pela conversa com o produtor real, não pela elegância do código. Cada hora gasta polindo o que ninguém usou ainda é hora roubada da fase 5 do plano. Codar com pressa controlada, mostrar cedo, ouvir mais.
