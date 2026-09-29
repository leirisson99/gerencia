# Data Model: Ciclo Aberto pelo Salário

Valores em centavos, `BIGINT`. Datas de lançamento são `date` (sem hora, fuso
`America/Sao_Paulo`). Timestamps são `timestamptz` em UTC. Mudanças vêm na migração Alembic
reversível `0003_lancamento_categorias_iniciais`.

## lancamento (nova)

| Campo | Tipo | Regras |
| --- | --- | --- |
| id | bigint, PK | identity |
| usuario_id | bigint, FK `usuario.id` | `ON DELETE CASCADE`; toda consulta filtra por ele |
| categoria_id | bigint, FK `categoria.id` | `ON DELETE RESTRICT`; categoria do mesmo usuário, ativa |
| data | date | obrigatório; salário ≤ hoje (SP); qualquer lançamento ≥ primeiro salário |
| valor | bigint | obrigatório; `CHECK (valor > 0)`; ≤ 99.999.999.999 (validado na API) |
| tipo | varchar(7) | `entrada` \| `saida`, CHECK; copiado de `categoria.tipo`, nunca enviado pelo cliente |
| descricao | varchar(200), null | opcional, sem espaços nas pontas; vazio vira null |
| status | varchar(9) | `previsto` \| `realizado`, CHECK; default `realizado`; na categoria "Salário" só `realizado` |
| conta_no_saldo | boolean | default `true` (usado pela feature de cartão; aqui sempre `true`) |
| criado_em | timestamptz | default now() |
| atualizado_em | timestamptz | atualizado em toda edição |

**Índices**: `(usuario_id, data)` para listar por ciclo e achar a menor data;
`(usuario_id, categoria_id, data)` para buscar as datas de salário.

**Fora desta feature** (entram com as features que os usam, por migração própria):
`forma_pagamento`, `recorrencia_id`, `divida_id`, `parcela_num`.

## categoria (existente, só dados novos)

Sem mudança de schema. A migração insere, para cada usuário existente, as categorias
iniciais; o cadastro (`services/auth.cadastrar`) passa a criá-las na mesma transação.

| Nome | Tipo | sistema |
| --- | --- | --- |
| Salário | entrada | true (já existia) |
| Renda extra | entrada | false |
| Moradia | saida | false |
| Alimentação | saida | false |
| Transporte | saida | false |
| Saúde | saida | false |
| Lazer | saida | false |
| Outros | saida | false |

A lista vive em `app/domain/categoria.py` (`CATEGORIAS_INICIAIS`). A migração usa uma cópia
literal da lista, para não depender do código da aplicação.

O `downgrade` apaga as categorias iniciais que não são de sistema (`sistema = false` e nome na
lista) e a tabela `lancamento`.

## Ciclo (derivado, nunca guardado)

`app/domain/ciclo.py`:

```text
Ciclo(inicio: date, fim: date | None)   # fim None = ciclo aberto
```

- Entrada: datas dos lançamentos de salário (`status = realizado`, categoria "Salário") do
  usuário, em qualquer ordem, com repetições.
- Datas distintas ordenadas `d1 < d2 < … < dn` geram os ciclos `[d1, d2−1]`, …,
  `[dn−1, dn−1]`, `[dn, None]`.
- Toda data `x ≥ d1` pertence a exatamente um ciclo; `x < d1` não pertence a nenhum.

## Invariante de cobertura

Depois de qualquer escrita em `lancamento`, para cada usuário:

```text
se existe lançamento que não é salário:
    existe ao menos um salário
    e min(data dos que não são salário) ≥ min(data dos salários)
```

Verificado por `verificar_cobertura` (domínio) antes de gravar, sob `SELECT … FOR UPDATE` na
linha do usuário ([research.md](research.md), R6 e R7).

## Transições que mudam ciclos

| Ação | Efeito nos ciclos | Pode ser recusada por |
| --- | --- | --- |
| Criar salário | abre ciclo na data (ou nada, se já há salário nessa data) | data futura |
| Editar data de salário | move o limite entre ciclos vizinhos | data futura; cobertura |
| Excluir salário | funde os ciclos vizinhos | cobertura |
| Trocar categoria para "Salário" | igual a criar salário | data futura; status previsto |
| Trocar categoria de "Salário" para outra | igual a excluir salário | cobertura |
| Criar/editar outro lançamento | nenhum | sem salário; data antes do primeiro ciclo |
