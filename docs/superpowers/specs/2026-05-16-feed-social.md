# HedgeFácil — Fase 8: Feed Social

**Data:** 2026-05-16  
**Objetivo:** Feed estilo Twitter para produtores rurais: seguir pessoas e culturas, postar atualizações, curtir e comentar. Interface simples com HTMX (sem reload).

---

## Arquitetura

Nova app `apps.feed` com 4 models, views HTMX-first, templates com cards de post. O feed é uma query Django que une posts de produtores seguidos + culturas seguidas + posts próprios. Filtro por cultura via chip/GET param.

**Não há notificações, não há repost/quote, não há mídia — apenas texto com tag de cultura.**

---

## 1. Models (`apps/feed/models.py`)

### `Post`
```python
class Post(Model):
    autor       = FK(Produtor, on_delete=CASCADE, related_name='posts')
    texto       = CharField(max_length=280)
    cultura     = CharField(max_length=20, choices=Cultura.choices, blank=True)
    criado_em   = DateTimeField(auto_now_add=True)
    curtidas    = ManyToManyField(Produtor, related_name='posts_curtidos', blank=True)

    class Meta:
        ordering = ['-criado_em']
```

### `Comentario`
```python
class Comentario(Model):
    post      = FK(Post, on_delete=CASCADE, related_name='comentarios')
    autor     = FK(Produtor, on_delete=CASCADE, related_name='comentarios')
    texto     = CharField(max_length=280)
    criado_em = DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['criado_em']
```

### `FollowProdutor`
```python
class FollowProdutor(Model):
    seguidor = FK(Produtor, on_delete=CASCADE, related_name='seguindo_produtores')
    seguido  = FK(Produtor, on_delete=CASCADE, related_name='seguidores')

    class Meta:
        unique_together = ['seguidor', 'seguido']
```

### `FollowCultura`
```python
class FollowCultura(Model):
    produtor = FK(Produtor, on_delete=CASCADE, related_name='seguindo_culturas')
    cultura  = CharField(max_length=20, choices=Cultura.choices)

    class Meta:
        unique_together = ['produtor', 'cultura']
```

---

## 2. URLs (`apps/feed/urls.py`)

```
app_name = 'feed'

''                            → feed (GET)
'post/'                       → novo_post (POST)
'post/<int:post_id>/curtir/'  → curtir (POST, HTMX)
'post/<int:post_id>/comentar/' → comentar (POST, HTMX)
'seguir/<int:produtor_id>/'   → seguir_produtor (POST, toggle)
'seguir-cultura/<str:cultura>/' → seguir_cultura (POST, toggle)
'perfil/<str:username>/'      → perfil (GET)
```

Montar em `core/urls.py`: `path('feed/', include('apps.feed.urls'))`

---

## 3. Views (`apps/feed/views.py`)

### `feed(request)`
```python
@login_required
def feed(request):
    seguindo_ids = FollowProdutor.objects.filter(
        seguidor=request.user
    ).values_list('seguido_id', flat=True)
    culturas_seguidas = FollowCultura.objects.filter(
        produtor=request.user
    ).values_list('cultura', flat=True)

    posts = Post.objects.filter(
        Q(autor=request.user) |
        Q(autor_id__in=seguindo_ids) |
        Q(cultura__in=culturas_seguidas)
    ).select_related('autor').prefetch_related('curtidas', 'comentarios__autor').distinct()

    cultura_filtro = request.GET.get('cultura', '')
    if cultura_filtro:
        posts = posts.filter(cultura=cultura_filtro)

    posts = posts[:50]

    culturas_seguidas_set = set(culturas_seguidas)
    return render(request, 'feed/feed.html', {
        'posts': posts,
        'cultura_filtro': cultura_filtro,
        'culturas_choices': Cultura.choices,
        'culturas_seguidas': culturas_seguidas_set,
    })
```

### `novo_post(request)`
POST only. Cria Post, retorna `feed/_post.html` fragment se HTMX, senão redirect feed.

### `curtir(request, post_id)`
POST only, `@login_required`. Toggle ManyToMany. Retorna fragment `feed/_curtir.html` com novo count.

### `comentar(request, post_id)`
POST only, `@login_required`. Cria Comentario. Retorna `feed/_comentarios.html` fragment.

### `seguir_produtor(request, produtor_id)`
POST only. Toggle FollowProdutor. Retorna fragment com botão atualizado.

### `seguir_cultura(request, cultura)`
POST only. Toggle FollowCultura. Retorna fragment com chip atualizado.

### `perfil(request, username)`
GET. Mostra posts do produtor + contadores (seguidores, seguindo). Botão seguir/desseguir.

---

## 4. Templates

```
templates/feed/
  feed.html              — layout principal (extends base.html)
  perfil.html            — perfil de produtor
  _post.html             — card de post (partial)
  _curtir.html           — botão curtir com count (partial)
  _comentarios.html      — lista + form de comentários (partial)
  _form_post.html        — textarea nova postagem
```

### `feed.html` estrutura
```
[_form_post.html]           ← textarea sticky no topo
[Chips de cultura]          ← "Todos | Soja | Milho | ..." filtra via GET
[lista de _post.html]       ← um por post
```

### `_post.html` estrutura
```
[Avatar inicial | @username | cultura tag | data]
[texto do post]
[❤ N curtidas (HTMX toggle) | 💬 N comentários (expandir)]
[comentários expandíveis + form novo comentário]
```

---

## 5. Navegação

- Sidebar: adicionar link `{% url 'feed:feed' %}` com ícone 🌐 antes de "Safras"
- Bottom bar: substituir "Safras" por "Feed" no slot 2, ou adicionar 5º item — decidir: **substituir o 4º item (Hedge) por Feed, e Hedge fica só no sidebar**. Não: manter 4 itens, Safras → Feed, Hedge no sidebar + deep link. **Decisão final: bottom bar = Posição | Feed | Vendas | Hedge. Safras fica só no sidebar.**

---

## 6. Registro da app e migrations

- Adicionar `'apps.feed'` em `INSTALLED_APPS`
- `python manage.py makemigrations feed`
- `python manage.py migrate`

---

## 7. Testes (`apps/feed/tests.py`)

### `FeedModelTestCase` (4 testes)
- `test_post_criado_com_sucesso`
- `test_follow_produtor_unique_together`
- `test_follow_cultura_unique_together`
- `test_comentario_vinculado_ao_post`

### `FeedViewTestCase` (7 testes)
- `test_feed_retorna_200`
- `test_feed_requer_login`
- `test_feed_mostra_posts_de_seguidos`
- `test_feed_mostra_posts_de_cultura_seguida`
- `test_feed_filtro_por_cultura`
- `test_feed_nao_mostra_posts_sem_relacao`
- `test_novo_post_cria_post`

### `CurtirComentarTestCase` (4 testes)
- `test_curtir_adiciona_curtida`
- `test_curtir_remove_curtida_existente`
- `test_comentar_cria_comentario`
- `test_comentar_requer_login`

### `FollowTestCase` (3 testes)
- `test_seguir_produtor_cria_follow`
- `test_seguir_produtor_toggle_remove`
- `test_seguir_cultura_cria_follow`

---

## 8. Contagem de testes

| Fase | Novos | Total |
|------|-------|-------|
| Baseline | — | 149 |
| Fase 8 | +18 | 167 |

---

## Arquivos criados/modificados

| Arquivo | Ação |
|---------|------|
| `apps/feed/__init__.py` | Criar |
| `apps/feed/models.py` | Criar |
| `apps/feed/views.py` | Criar |
| `apps/feed/urls.py` | Criar |
| `apps/feed/tests.py` | Criar |
| `apps/feed/apps.py` | Criar |
| `templates/feed/feed.html` | Criar |
| `templates/feed/perfil.html` | Criar |
| `templates/feed/_post.html` | Criar |
| `templates/feed/_curtir.html` | Criar |
| `templates/feed/_comentarios.html` | Criar |
| `templates/feed/_form_post.html` | Criar |
| `core/settings.py` | Adicionar `apps.feed` |
| `core/urls.py` | Adicionar `feed/` include |
| `templates/partials/_sidebar.html` | Adicionar link Feed |
| `templates/partials/_bottom_bar.html` | Substituir Safras por Feed |
