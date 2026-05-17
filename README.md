# HedgeFácil

Sistema de gestão de hedge para produtores rurais brasileiros. Permite cadastrar safras, registrar vendas antecipadas e acompanhar a posição de preço com linguagem simples — sem jargão financeiro.

## O que faz

- **Painel de posição**: cotação ao vivo da soja (CME via yfinance), histórico 30 dias, quanto já foi vendido e quanto ainda está exposto ao mercado
- **Gestão de safras**: cadastro de cultura, produção estimada, custo por saca e safra ativa
- **Registro de vendas**: contratos a termo, CPR, venda balcão, futuro B3, opção B3 — com cálculo de receita travada e preço médio ponderado
- **Cenários de preço**: simula o impacto de altas e quedas de -50% a +30% no saldo ainda a vender
- **Estratégias de hedge**: compara put comprada, futuro vendido e collar com gráfico de P&L interativo
- **Opções disponíveis no mercado**: chain de puts reais da CME (soja/milho/café) em BRL/saca, com 3 cards de proteção em linguagem de produtor, simulador de custo e seção avançada com volatilidade implícita e greeks explicados

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Backend | Django 6 + Python 3.12 |
| Banco | PostgreSQL (SQLite em dev) |
| Dados de mercado | yfinance — CME ZS=F, ZC=F, KC=F |
| Frontend | Tailwind CSS (CDN) + JS vanilla + Chart.js |
| Auth | django-sesame (magic link) |
| Deploy | gunicorn + whitenoise |

## Estrutura de apps

```
apps/
  contas/    # modelo Produtor (AbstractUser), login/registro
  safra/     # modelo Safra (cultura, produção, custo, safra ativa)
  vendas/    # modelo Venda (tipo, sacas, preço, contraparte)
  posicao/   # cotação ao vivo, cálculo de posição, risco, chain de opções CME
  hedge/     # cenários, estratégias Black-Scholes, view de opções reais
```

## URLs principais

| Rota | Descrição |
|------|-----------|
| `/` | Login / registro |
| `/painel/` | Painel de posição com cotação ao vivo |
| `/safra/` | Lista de safras |
| `/vendas/<id>/` | Lista e cadastro de vendas da safra |
| `/hedge/<id>/cenarios/` | Cenários de preço |
| `/hedge/<id>/estrategias/` | Gráfico de estratégias de hedge |
| `/hedge/<id>/opcoes/` | Opções reais CME em BRL/saca |

## Módulo de opções (Fase 8)

Busca chains de puts reais via `yfinance` para ZS=F (soja), ZC=F (milho) e KC=F (café). Converte strikes e prêmios de centavos/bushel para R$/saca usando câmbio ao vivo.

**Conversão:** `preço_brl_saca = strike_usd_cents × (60/27.2155) × USDBRL / 100`

Exibe 3 cards de proteção ancorados no custo da safra:
- **Proteção Mínima** — put mais próxima de 90% do custo
- **Proteção do Custo** — put mais próxima do break-even
- **Proteção Total** — put ATM (mais próxima da cotação atual)

Simulador JS calcula custo total e resultado em diferentes cenários sem chamadas ao servidor.

Seção avançada (expansível) mostra tabela completa de puts com volatilidade implícita em linguagem de produtor ("nervosismo do mercado") e delta/theta explicados em português.

Cache: câmbio + vencimentos + puts com TTL de 1 hora por `(cultura, vencimento)`.

## Rodando localmente

```bash
# dependências
pip install -r requirements.txt

# banco
python manage.py migrate

# servidor
python manage.py runserver
```

Variáveis de ambiente (arquivo `.env`):

```
DEBUG=True
SECRET_KEY=sua-chave-aqui
DATABASE_URL=postgres://user:pass@localhost/hedgefacil  # opcional, usa SQLite sem isso
```

## Testes

```bash
python manage.py test
```

164 testes. Cobertura: serviços de cotação/posição, cálculos Black-Scholes, chain de opções CME, view de opções, cenários, estratégias, registro de safras e vendas, autenticação.
