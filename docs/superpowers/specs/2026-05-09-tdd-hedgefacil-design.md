# HedgeFácil — Plano de Desenvolvimento com TDD

**Data:** 2026-05-09
**Objetivo:** Aprender TDD do zero enquanto desenvolve o HedgeFácil end-to-end.
**Abordagem:** Mini-Sprints TDD — segue o roadmap original, aplicando o ciclo Red-Green-Refactor em cada passo.

---

## 1. Ciclo TDD e Estrutura de Sessão

O ciclo Red-Green-Refactor repetido em cada sessão:

```
1. RED      → escreve um teste que falha (código ainda não existe)
2. GREEN    → escreve o mínimo de código para o teste passar
3. REFACTOR → melhora o código sem quebrar o teste
```

**Regra absoluta:** nunca escreve código de produção sem um teste falhando antes.

**Estrutura de cada sessão (1-2h):**
```
[10 min]  Revisão da sessão anterior
[60 min]  2-4 ciclos TDD completos
[10 min]  Commit + anotação do que fica para próxima sessão
```

**Ferramentas:**
- `python manage.py test` — roda todos os testes
- `python manage.py test tests.test_calculos` — roda só os cálculos
- `unittest.TestCase` — testes puros sem banco
- `django.test.TestCase` — testes com banco (models, views)

---

## 2. Organização dos Testes

```
tests/
  test_calculos.py   → services de posicao e hedge (sem banco)
  test_modelos.py    → propriedades e validações de Produtor, Safra, Venda

apps/contas/tests.py   → autenticação e login mágico
apps/vendas/tests.py   → views e forms de vendas
apps/posicao/tests.py  → view do painel
apps/hedge/tests.py    → views de cenários e proteção
```

**Padrão de nomenclatura:**

```python
class CalcularPosicaoTestCase(TestCase):
    def setUp(self):
        # estado mínimo para o teste

    def test_preco_medio_ponderado_com_duas_vendas(self):
        # Arrange → Act → Assert
```

**Três tipos de teste:**

| Tipo | Herda de | Usa banco? | Onde usar |
|---|---|---|---|
| Unitário puro | `unittest.TestCase` | Não | `simular_cenarios` (hedge) — função pura com parâmetros Decimal |
| Model/service test | `django.test.TestCase` | Sim | `calcular_posicao`, propriedades de Safra/Venda, constraints |
| View test | `django.test.TestCase` | Sim | status codes, contexto de template |

---

## 3. Mini-Sprints com Sessões TDD

A ordem dentro de cada sprint é sempre:
**test model → model → test service → service → test view → view**

### Sprint 1 — Fundação (3 sessões)

**Sessão 1 — Produtor model**
```
RED:   test_produtor_tem_campos_extras()         # whatsapp, cidade, estado
RED:   test_produtor_str_retorna_username()
GREEN: implementa Produtor(AbstractUser)
RED:   test_produtor_aceitou_termos_nulo_por_padrao()
GREEN: campo aceitou_termos_em
```

**Sessão 2 — Login mágico (django-sesame)**
```
RED:   test_solicitar_login_envia_email()
RED:   test_solicitar_login_cria_produtor_se_nao_existe()
GREEN: view solicitar_login + configuração sesame
```

**Sessão 3 — Infraestrutura (sem TDD)**
```
base.html, header, bottom bar, deploy Railway
Testes manuais de navegação e responsividade mobile
```

### Sprint 2 — Safra e Vendas (4 sessões)

**Sessão 4 — Safra model**
```
RED:   test_safra_custo_total_multiplica_producao_por_custo()
RED:   test_safra_unique_por_produtor_cultura_ano()
RED:   test_safra_str_formato_correto()
GREEN: implementa Safra
```

**Sessão 5 — Venda model**
```
RED:   test_venda_receita_usa_decimal_nao_float()
RED:   test_venda_str_formato_correto()
GREEN: implementa Venda
```

**Sessão 6 — CRUD de Venda (views)**
```
RED:   test_criar_venda_post_valido_redireciona()
RED:   test_criar_venda_post_invalido_retorna_form_com_erros()
RED:   test_listar_vendas_retorna_200()
GREEN: views + VendaForm
```

**Sessão 7 — HTMX**
```
RED:   test_htmx_request_em_criar_venda_retorna_fragmento()
RED:   test_request_normal_redireciona()
GREEN: detecta request.htmx, retorna _lista.html vs redirect
```

### Sprint 3 — Painel de Posição (2 sessões)

**Sessão 8 — posicao/services.py**
```
RED:   test_preco_medio_ponderado_com_duas_vendas()
RED:   test_percentual_vendido_zero_quando_sem_vendas()
RED:   test_sacas_a_vender_correto()
RED:   test_lucro_parcial_correto()
RED:   test_receita_travada_soma_todas_vendas()
GREEN: calcular_posicao() completo
REFACTOR: extrai helpers se necessário
```

**Sessão 9 — view /painel/**
```
RED:   test_painel_retorna_200_para_usuario_logado()
RED:   test_painel_redireciona_usuario_sem_safra()
RED:   test_painel_contexto_tem_posicao_safra()
GREEN: view painel + template
```

### Sprint 4 — Hedge (2 sessões)

**Sessão 10 — hedge/services.py**
```
RED:   test_cenario_queda_20_reduz_receita_corretamente()
RED:   test_cenario_estavel_impacto_zero()
RED:   test_cenario_alta_15_aumenta_receita()
RED:   test_simular_cenarios_retorna_3_por_padrao()
GREEN: simular_cenarios() completo
```

**Sessão 11 — views de hedge**
```
RED:   test_view_cenarios_renderiza_3_cenarios()
RED:   test_view_cenarios_requer_login()
GREEN: view /hedge/<id>/cenarios/ + /hedge/<id>/proteger/
```

### Sprint 5 — Polimento (2 sessões)

**Sessões 12-13**
```
Cotação estática, exportação PDF, onboarding
Smoke tests manuais end-to-end com produtor real
```

---

## 4. Guia Prático para TDD Zero

**Roteiro mental antes de cada ciclo:**
> "O que esse código deve fazer? Qual é o resultado esperado?"

Escreva a resposta como um teste. Exemplo real:

```python
# PASSO 1: RED  (usa django.test.TestCase — precisa de banco para safra.vendas.all())
def test_preco_medio_ponderado_com_duas_vendas(self):
    produtor = Produtor.objects.create_user(username="ze", email="ze@teste.com")
    safra = Safra.objects.create(
        produtor=produtor, cultura="soja", ano_safra="2025/26",
        producao_estimada_sacas=Decimal("1000"), custo_por_saca=Decimal("80"),
    )
    Venda.objects.create(safra=safra, tipo="balcao", contraparte="Cargill",
        sacas=Decimal("300"), preco_por_saca=Decimal("120"), data_negociacao="2025-03-01")
    Venda.objects.create(safra=safra, tipo="balcao", contraparte="Cargill",
        sacas=Decimal("200"), preco_por_saca=Decimal("140"), data_negociacao="2025-04-01")

    posicao = calcular_posicao(safra)

    self.assertEqual(posicao.preco_medio_ponderado, Decimal("128.00"))

# PASSO 2: GREEN — implementa o mínimo para passar
# PASSO 3: REFACTOR — limpa sem quebrar
```

**Os 3 erros mais comuns (para evitar):**
1. Escrever código antes do teste — resiste à tentação toda sessão
2. Escrever vários testes de uma vez — um por ciclo, ciclo completo antes do próximo
3. Refatorar no passo GREEN — no verde, só o mínimo

**Sinal de que o ciclo está funcionando:**
- Você sabe exatamente por que o teste falhou (mensagem de erro clara)
- O código para passar o teste é pequeno (menos de 10 linhas normalmente)
- Após refatorar, todos os testes ainda passam

---

## 5. Critério de Conclusão da Fase 1

A fase 1 termina quando um produtor real, sem ajuda, consegue:

1. Criar conta com email
2. Cadastrar a safra atual
3. Lançar 3 vendas reais
4. Ver o painel com preço médio correto
5. Ver os cenários de queda/alta no saldo a vender
6. Clicar no WhatsApp e chamar

**E os testes garantem:**
- `calcular_posicao` nunca retorna resultado errado
- `simular_cenarios` nunca usa float em vez de Decimal
- Venda nunca é salva sem safra associada
