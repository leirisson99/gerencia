# Data Model: Dívidas com Parcelas

Migração reversível `0007_divida`.

## divida (nova)

| Campo | Tipo | Regras |
| --- | --- | --- |
| id | bigint, PK | identity |
| usuario_id | bigint, FK `usuario.id` | CASCADE, indexado |
| categoria_id | bigint, FK `categoria.id` | RESTRICT; tipo compatível com a direção |
| descricao | varchar(200) | obrigatório |
| pessoa | varchar(120) | obrigatório |
| direcao | varchar(9) | `devo` \| `me_devem` |
| valor_total | bigint | `> 0` e `>= parcelas` |
| parcelas | smallint | 1–120 |
| forma_pagamento | varchar(8) | `pix` \| `boleto` \| `cartao` \| `dinheiro`; `cartao` só com `devo` |
| dia_vencimento | smallint | 1–31 |
| data_inicio | date | |
| criado_em | timestamptz | |

## lancamento (existente)

- `divida_id` bigint null, FK `divida.id` RESTRICT; `parcela_num` smallint null.
- CHECK `(divida_id IS NULL) = (parcela_num IS NULL)`; UNIQUE `(divida_id, parcela_num)`.

## Regras puras (`domain/parcelas.py`)

- `dividir(total, n)`: `n − 1` parcelas de `total // n` e a última com `total // n + total % n`.
- `datas_das_parcelas(dia, inicio, n)`: 1ª = `data_prevista(dia, inicio)`; k-ésima = mesmo dia
  `k − 1` meses depois, limitado ao fim do mês.
- `situacao([(valor, paga)])`: pagas, total, valor pago, restante, quitada.
