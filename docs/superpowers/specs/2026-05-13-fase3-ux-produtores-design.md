# HedgeFácil — Fase 3: UX Produtores

**Data:** 2026-05-13
**Objetivo:** Editar/deletar vendas + navegação entre múltiplas safras.

---

## 1. Editar Venda

**URL:** `vendas/<int:venda_id>/editar/`

**View `editar(request, venda_id)`:**
- `@login_required`
- Ownership: `get_object_or_404(Venda, id=venda_id, safra__produtor=request.user)`
- GET: retorna `_form.html` pré-preenchido (parcial para HTMX, mesmo template de `nova`)
- POST válido: atualiza e retorna `_lista.html` se HTMX, senão redireciona para `vendas:lista`
- POST inválido: retorna `_form.html` com erros

**Template `_lista.html`:** adiciona botão editar em cada item via HTMX get.

**Testes (6):** requer_login, get_200, get_404_outro_usuario, post_valido_atualiza, post_valido_redireciona, post_invalido_permanece.

---

## 2. Deletar Venda

**URL:** `vendas/<int:venda_id>/deletar/`

**View `deletar(request, venda_id)`:**
- `@require_POST` + `@login_required`
- Ownership: `get_object_or_404(Venda, id=venda_id, safra__produtor=request.user)`
- Deleta e retorna `_lista.html` (todas as vendas da safra) se HTMX, senão redireciona
- `safra` é recuperado da venda antes de deletar (para renderizar a lista atualizada)

**Template `_lista.html`:** adiciona botão deletar com `hx-post` + `hx-confirm`.

**Testes (4):** requer_login, post_deleta_venda, post_404_outro_usuario, get_nao_permitido (405).

---

## 3. Lista de Safras + Ativar

**URLs:**
- `safra/` → `lista` (GET)
- `safra/<int:safra_id>/ativar/` → `ativar` (POST)

**View `lista(request)`:**
- `@login_required`
- Mostra todas as safras do produtor (ordenadas por `-criada_em`)
- Mostra qual está ativa

**View `ativar(request, safra_id)`:**
- `@require_POST` + `@login_required`
- `get_object_or_404(Safra, id=safra_id, produtor=request.user)`
- Seta `ativa=True` na safra selecionada, `ativa=False` em todas as outras do mesmo produtor (transação atômica)
- Redireciona para `posicao:painel`

**Template `safra/lista.html`:**
- Lista cada safra com nome, data, status (Ativa / Inativa)
- Botão "Ativar" (POST, desabilitado para a já ativa)
- Link "Nova safra"

**Painel:** adicionar link "Trocar safra" abaixo do nome da safra.

**Testes (7):** lista_requer_login, lista_200, lista_mostra_safras_do_usuario, lista_nao_mostra_safras_de_outros, ativar_requer_login, ativar_muda_safra_ativa, ativar_redireciona_para_painel.

---

## Arquivos a modificar/criar

| Arquivo | Ação |
|---------|------|
| `apps/vendas/views.py` | Add `editar`, `deletar` |
| `apps/vendas/urls.py` | Add `<id>/editar/`, `<id>/deletar/` |
| `apps/vendas/tests.py` | Add 10 testes |
| `templates/vendas/_lista.html` | Add editar/deletar buttons |
| `apps/safra/views.py` | Add `lista`, `ativar` |
| `apps/safra/urls.py` | Add `""`, `<id>/ativar/` |
| `apps/safra/tests.py` | Add 7 testes |
| `templates/safra/lista.html` | Criar |
| `templates/posicao/painel.html` | Add link "Trocar safra" |

## Contagem de testes

Baseline: 89. Meta: ~106 (+17 novos).
