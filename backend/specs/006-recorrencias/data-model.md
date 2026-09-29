# Data Model: Recorrências

Migração reversível `0006_recorrencia`.

## recorrencia (nova)

| Campo | Tipo | Regras |
| --- | --- | --- |
| id | bigint, PK | identity |
| usuario_id | bigint, FK `usuario.id` | CASCADE, indexado |
| categoria_id | bigint, FK `categoria.id` | RESTRICT; do usuário, ativa, não "Salário" |
| descricao | varchar(200) | obrigatório, sem espaços nas pontas |
| valor | bigint | `CHECK (valor > 0)`; centavos |
| tipo | varchar(7) | `entrada` \| `saida`; copiado da categoria |
| dia | smallint | `CHECK (dia BETWEEN 1 AND 31)` |
| ativa | boolean | default true |
| criado_em | timestamptz | default now() |

## lancamento (existente)

- Nova coluna `recorrencia_id` bigint null, FK `recorrencia.id` RESTRICT.
- Índice `(recorrencia_id, data)` para a checagem "já gerado neste ciclo".

## Regra pura

`data_prevista(dia, inicio)`: candidato no mês de `inicio` com `min(dia, último dia do mês)`;
se for antes de `inicio`, usa o mês seguinte com a mesma limitação.
