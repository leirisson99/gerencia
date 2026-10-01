# Implementation Plan: Serviços a Receber

**Branch**: `013-servicos-a-receber` | **Date**: 2026-09-30 | **Spec**: [spec.md](spec.md)

## Summary

Tabela `servico` ligada a exatamente um lançamento de entrada (`servico.lancamento_id`, único),
no mesmo padrão de `casa.lancamento_id`. Criar grava serviço + lançamento previsto numa
transação; receber/desfazer mudam só o lançamento; editar/excluir só enquanto previsto. A
situação (`a_receber`, `atrasado`, `recebido`) é função pura em `domain/servico.py`. Rotas em
`/api/v1/servicos`, protegidas por uma dependência que recusa `clt` com 403. O lançamento ganha
`servico_id` (`column_property`) e fica travado em `/lancamentos` enquanto o dono tiver acesso a
serviços. A troca para `clt` com serviço pendente é recusada no domínio da troca (feature 012).

## Technical Context

**Language/Version**: Python 3.14

**Primary Dependencies**: as mesmas (FastAPI, SQLAlchemy 2, Pydantic v2, Alembic)

**Storage**: PostgreSQL 17 — tabela `servico` (migração `0013`)

**Testing**: `tests/domain/test_servico.py`, `tests/domain/test_ciclo.py` (troca);
`tests/api/test_servicos.py` (novo), ajuste em `tests/api/test_isolamento.py`

**Project Type**: web service (só backend)

**Performance Goals**: listagem com uma consulta (serviço + lançamento); volume pequeno por
usuário, filtro de situação aplicado em Python sobre o resultado já ordenado

**Constraints**: nenhum comportamento da 012 muda para quem não usa serviços

## Constitution Check

| Princípio | Verificação | Status |
| --- | --- | --- |
| I. Integridade financeira | Valores em centavos `int`; o saldo continua vindo só do lançamento (previsto não conta); serviço + lançamento gravados numa transação; o valor recebido fica no lançamento, o combinado no serviço — nada conta duas vezes. | ✅ |
| II. Ciclo | Nada de ciclo guardado; `clt_prestador` passa pela cobertura de ciclo (`verificar_novos_lancamentos`) ao criar, editar, receber e desfazer. | ✅ |
| III. Teste primeiro | `situacao`, `descricao_do_lancamento`, `tem_servicos` e a troca com pendentes testados antes, com data prevista ontem/hoje/amanhã e descrição no limite de 200. | ✅ |
| IV. Contratos | Schemas tipados (`ServicoIn`, `ServicoPatch`, `RecebimentoIn`, `ServicoOut`); `LancamentoOut.servico_id` aditivo; erros 403/404/409/422 no formato único ([contracts/api.md](contracts/api.md)). | ✅ |
| V. Isolamento | Toda consulta filtra por `usuario_id`; serviço de outro → 404, com teste também em `test_isolamento.py`. | ✅ |
| VI. Escopo | Previsto pela constituição 4.3.0 e pedido explícito. Um pagamento por serviço; sem cadastro de clientes, cobrança ou lembrete. Lançamento continua só com valor, categoria e data obrigatórios. | ✅ |

**Resultado**: sem violações. Reavaliado após o desenho: sem mudanças.

## Project Structure

### Documentation

```text
specs/013-servicos-a-receber/
├── plan.md, research.md, data-model.md, quickstart.md
├── contracts/api.md
└── tasks.md            # /speckit-tasks
```

### Source Code

```text
backend/
├── alembic/versions/0013_servico.py
├── app/domain/usuario.py           # + tem_servicos
├── app/domain/servico.py           # situacao, descricao_do_lancamento
├── app/domain/ciclo.py             # troca: + SERVICOS_PENDENTES
├── app/models/servico.py           # Servico
├── app/models/lancamento.py        # + servico_id (column_property)
├── app/schemas/servico.py          # ServicoIn, ServicoPatch, RecebimentoIn, ServicoOut
├── app/schemas/lancamento.py       # + servico_id em LancamentoOut
├── app/services/servico.py         # criar, listar, obter, editar, excluir, receber, desfazer
├── app/services/lancamento.py      # trava do lançamento de serviço
├── app/services/perfil.py          # troca para clt com pendentes → 409
├── app/api/deps.py                 # ComServicosDep (403 perfil_sem_servicos)
├── app/api/routes/servicos.py
├── app/main.py                     # include_router
└── tests/domain/test_servico.py, tests/api/test_servicos.py
```

**Structure Decision**: monólito FastAPI, como nas features anteriores. Regras puras em
`domain/`; `services/servico.py` orquestra serviço + lançamento numa transação.

## Decisões

Detalhes e alternativas em [research.md](research.md).

- **Ligação**: `servico.lancamento_id` único e obrigatório; excluir apaga o serviço e depois o
  lançamento, na mesma transação.
- **Recebimento**: muda o lançamento para realizado com data e valor recebidos; o serviço não
  muda. Desfazer volta a previsto em `data_prevista` com `servico.valor`.
- **Trava**: em `/lancamentos`, lançamento de serviço não muda valor, status, categoria nem data
  e não é excluído (422/409), só se o dono tiver acesso a serviços; descrição continua livre.
- **Acesso**: dependência de rota `ComServicosDep`, depois da autenticação.
- **Troca**: `verificar_troca_tipo_renda` ganha `servicos_pendentes` e devolve
  `SERVICOS_PENDENTES` (antes dos outros problemas) quando o novo tipo não tem serviços.

## Complexity Tracking

Sem violações.
