# Data Model: Serviços a Receber

## servico (nova)

| Campo | Tipo | Regras |
| --- | --- | --- |
| id | `BIGINT IDENTITY` | PK |
| usuario_id | `BIGINT` | FK `usuario.id` `ON DELETE CASCADE`, índice |
| categoria_id | `BIGINT` | FK `categoria.id` `ON DELETE RESTRICT`; ativa, `tipo = 'entrada'`, não "Salário" (validado no serviço) |
| cliente | `VARCHAR(120) NOT NULL` | obrigatório, sem espaços nas pontas |
| descricao | `VARCHAR(200) NULL` | opcional; vazio vira `NULL` |
| valor | `BIGINT NOT NULL` | centavos, `CHECK (valor > 0)` |
| data_prevista | `DATE NOT NULL` | pode ser passada |
| lancamento_id | `BIGINT NOT NULL UNIQUE` | FK `lancamento.id` `ON DELETE RESTRICT` |
| criado_em | `TIMESTAMPTZ NOT NULL` | |

Migração `0013_servico.py` com `downgrade` (drop table).

## lancamento (sem mudança de schema)

- `servico_id` (`column_property`, só leitura): id do serviço ligado, ou `NULL`.

## Situação (derivada, `domain/servico.py`)

| Lançamento | data_prevista vs hoje | Situação |
| --- | --- | --- |
| realizado | qualquer | `recebido` |
| previsto | `< hoje` | `atrasado` |
| previsto | `>= hoje` | `a_receber` |

## Transições

| Ação | Pré-condição | Efeito no lançamento |
| --- | --- | --- |
| criar | categoria válida; cobertura (clt_prestador) | novo previsto: valor, categoria, `data_prevista`, descrição gerada |
| editar | não recebido | previsto acompanha valor, data, categoria, descrição |
| receber | não recebido; `data <= hoje` | realizado, `data`, `valor` (padrão `servico.valor`) |
| desfazer | recebido | previsto, `data_prevista`, `servico.valor` |
| excluir | não recebido | serviço e lançamento removidos |

## Troca de tipo de renda (extensão da 012)

`verificar_troca_tipo_renda(..., servicos_pendentes)`: se o novo tipo não tem serviços
(`clt`) e há serviço não recebido → `SERVICOS_PENDENTES`, antes das outras verificações.
