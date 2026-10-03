# Data Model: Carteiras PF e PJ (019)

Todo valor monetário continua `int` em centavos.

## `usuario` (alteração)

| Campo | Tipo | Regra |
| --- | --- | --- |
| `tem_pj` | boolean, `server_default false` | Só pode ser `true` com `tipo_renda` em (`prestador`, `clt_prestador`) |

## `lancamento` (alteração)

| Campo | Tipo | Regra |
| --- | --- | --- |
| `carteira` | varchar(2), `server_default 'pf'`, `CHECK carteira IN ('pf', 'pj')` | Opcional na entrada; ausente = `pf` |

- Índice `ix_lancamento_usuario_data` (`usuario_id, data`) passa a ser
  `ix_lancamento_usuario_carteira_data` (`usuario_id, carteira, data`).
- Na PJ: a categoria "Salário" é recusada.
- Na PJ, nesta fase, só lançamentos avulsos, de recorrência ou de retirada; parcela de dívida,
  depósito de cartela, serviço e importação continuam `pf` (FR-015).

## `recorrencia` (alteração)

| Campo | Tipo | Regra |
| --- | --- | --- |
| `carteira` | varchar(2), `server_default 'pf'`, `CHECK` | Os previstos gerados herdam a carteira |

## Nova tabela `retirada`

| Campo | Tipo | Regra |
| --- | --- | --- |
| `id` | bigint identity, PK | |
| `usuario_id` | bigint, FK `usuario.id` `ON DELETE CASCADE`, índice | Dono |
| `data` | date | ≤ hoje (São Paulo) |
| `valor` | bigint, `CHECK valor > 0` | Centavos |
| `lancamento_pj_id` | bigint, FK `lancamento.id` `ON DELETE RESTRICT`, único | Saída, carteira `pj`, categoria "Retirada para PF" |
| `lancamento_pf_id` | bigint, FK `lancamento.id` `ON DELETE RESTRICT`, único | Entrada, carteira `pf`, categoria "Pró-labore e lucros" |
| `criado_em` | timestamptz | |

Invariantes, testadas em `tests/domain/test_retirada.py` e na API:

- os dois lados têm o mesmo `valor` e a mesma `data` da retirada, `status = realizado` e
  `conta_no_saldo = True`;
- editar a retirada atualiza os dois lados na mesma transação; excluir apaga a retirada e
  depois os dois lados;
- o lado PF segue a cobertura por salário da PF (`clt_prestador`).

## Categorias de sistema novas

| Nome | Tipo | Quando |
| --- | --- | --- |
| Retirada para PF | saida | Ao ligar a PJ (idempotente) |
| Pró-labore e lucros | entrada | Ao ligar a PJ (idempotente) |

Elas são protegidas por `edicao_permitida` (sistema). Ver research R5 para o conflito de nome.

## `evento_uso` (alteração de `CHECK`)

Tipos novos: `retirada_feita`, `retirada_editada`, `retirada_excluida`.

## Regras puras (domínio)

| Função | Arquivo | Regra |
| --- | --- | --- |
| `ciclo_pelo_mes(tipo_renda, carteira="pf")` | `domain/usuario.py` | `carteira == "pj"` ou `tipo_renda == "prestador"` |
| `pode_ter_pj(tipo_renda)` | `domain/usuario.py` | `prestador` ou `clt_prestador` |
| `verificar_pj(tem_pj_novo, tipo_novo, tem_dados_pj)` | `domain/usuario.py` | Devolve o problema (`tipo_sem_pj`, `pj_com_dados`) ou `None` |
| `validar_retirada(valor, data, hoje)` | `domain/retirada.py` | `valor > 0` e `data ≤ hoje` |
| `lados_da_retirada(valor, data)` | `domain/retirada.py` | Os dois movimentos (pj/saida, pf/entrada), mesmo valor e data |

`domain/saldo.resumir` não muda: recebe só os movimentos da carteira.

## Migração

`0018_carteira_pj.py` (ver research R12).
