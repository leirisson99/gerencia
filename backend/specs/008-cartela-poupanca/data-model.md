# Data Model: Cartela de Poupança

Migração reversível `0008_cartela`.

## cartela (nova)

| Campo | Tipo | Regras |
| --- | --- | --- |
| id | bigint, PK | identity |
| usuario_id | bigint, FK `usuario.id` | CASCADE, indexado |
| nome | varchar(80) | obrigatório |
| meta | bigint | `> 0`, centavos |
| valor_base | bigint | `> 0`, `<= meta` |
| criada_em | timestamptz | |

## casa (nova)

| Campo | Tipo | Regras |
| --- | --- | --- |
| id | bigint, PK | identity |
| cartela_id | bigint, FK `cartela.id` | CASCADE |
| valor | bigint | `> 0` |
| ordem | smallint | 1…N (+1 para o ajuste); UNIQUE com `cartela_id` |
| is_ajuste | boolean | |
| depositado_em | date, null | null = livre |
| lancamento_id | bigint, FK `lancamento.id`, null | UNIQUE; CHECK `(depositado_em IS NULL) = (lancamento_id IS NULL)` |

## categoria (dados)

"Poupança" (`saida`, `sistema = true`) para todos os usuários; inserida pela migração para quem
não tem e criada no cadastro.

## Regras puras (`domain/cartela.py`)

- `gerar_casas(meta, base)`: N máximo com `base × N(N+1)/2 ≤ meta`; casas `base × k` (k = 1…N) e
  ajuste `meta − base × N(N+1)/2` se > 0.
- `progresso(casas, meta)`: guardado, falta, percentual inteiro (`guardado × 100 // meta`),
  maior casa livre.
