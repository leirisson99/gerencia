# Data Model: Limite por Categoria

## `categoria` (alterada, migração `0009`)

| Campo | Tipo | Regra |
| --- | --- | --- |
| `limite` | `BIGINT NULL` | centavos; `CHECK (limite > 0)`; só em categoria de saída (serviço) |

Sem histórico: mudar o limite muda a situação de todos os ciclos, inclusive fechados.

## Derivados (não guardados)

- **Usado no ciclo**: soma dos lançamentos da categoria no ciclo com `status = realizado` e
  `conta_no_saldo = true` (mesmo filtro do saldo).
- **Situação**: `ok` (usado < 80% do limite), `atencao` (80% a 100% inclusive), `estourado`
  (acima de 100%). Ordem para "piorou": `ok < atencao < estourado`.
- **Aviso de limite**: `{categoria_id, nome, usado, limite, situacao}`, só na resposta de
  `POST`/`PATCH /lancamentos` quando a situação piora no ciclo da data do lançamento.
