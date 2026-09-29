# Implementation Plan: Ciclo Aberto pelo Salário

**Branch**: `001-ciclo-salario` | **Date**: 2026-09-28 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-ciclo-salario/spec.md`

## Summary

O salário, lançado à mão na categoria de sistema "Salário", abre um ciclo que vai até a véspera
do próximo salário. A feature cria a tabela `lancamento`, as categorias iniciais de cada
usuário, o CRUD de lançamentos com a regra de cobertura (nenhum lançamento fora de ciclo) e as
consultas de ciclo (atual, por data, lançamentos do ciclo, sugestão do valor do salário).
Ciclos são derivados das datas dos salários por funções puras em `app/domain/ciclo.py`; nada de
ciclo é guardado. Decisões em [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.14 (venv em `backend/.venv`)

**Primary Dependencies**: FastAPI, Pydantic v2, SQLAlchemy 2.x síncrono, psycopg 3, Alembic
(os mesmos da 002; nenhuma dependência nova)

**Storage**: PostgreSQL 17 — nova tabela `lancamento`, dados novos em `categoria`
([data-model.md](data-model.md))

**Testing**: pytest — `tests/domain/test_ciclo.py` (regras puras) e `tests/api/`
(`test_categorias.py`, `test_lancamentos.py`, `test_ciclos.py`) contra PostgreSQL real

**Target Platform**: servidor Linux (container) atrás de HTTPS

**Project Type**: web service (API HTTP); escopo só do backend

**Performance Goals**: cada rota responde em menos de 1 s; derivar ciclos lê só as datas de
salário do usuário (~12 por ano), com índice

**Constraints**: dinheiro em centavos `int`; ciclo nunca guardado; toda consulta filtrada
pelo usuário; escritas de lançamento serializadas por usuário (`SELECT … FOR UPDATE`)

**Scale/Scope**: 9 rotas, 1 tabela nova, 1 migração (`0003`)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Verificação | Status |
| --- | --- | --- |
| I. Integridade Financeira | `valor` é `StrictInt` > 0 na API e `BIGINT` com `CHECK (valor > 0)`; `conta_no_saldo` existe com default `true`; escritas numa transação. | ✅ |
| II. Ciclo Aberto pelo Salário | Ciclo derivado em `domain/ciclo.py` das datas dos salários; nenhuma tabela/coluna de ciclo; outros lançamentos recusados antes do primeiro salário; salário só lançado à mão. | ✅ |
| III. Domínio Puro e Teste Primeiro | `montar_ciclos`, `ciclo_da_data`, `ciclo_atual`, `verificar_cobertura` puras, testadas antes (virada de ano, mesmo dia, ciclo aberto, primeiro ciclo, exclusão/mudança de salário); API testada em PostgreSQL. | ✅ |
| IV. API com Contratos Tipados | Schemas de entrada e saída, `extra="forbid"`, `tipo` derivado da categoria; novos códigos de erro no formato único ([contracts/api.md](contracts/api.md)). | ✅ |
| V. Contas e Isolamento | Lançamento e categoria de outro usuário → 404 (com teste); ciclos só com salários do próprio usuário. | ✅ |
| VI. Escopo P0 e Simplicidade | Lançamento só com valor, categoria e data obrigatórios; campos de dívida/recorrência/forma de pagamento ficam para as features que os usam; sem gancho de recorrências (FR-011 adiado, R12). | ✅ |

**Resultado**: sem violações; reavaliado após o desenho, sem mudanças.

## Project Structure

### Documentation (this feature)

```text
specs/001-ciclo-salario/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/api.md
└── tasks.md
```

### Source Code

```text
backend/
├── alembic/versions/0003_lancamento_categorias_iniciais.py
├── app/
│   ├── domain/
│   │   ├── ciclo.py            # Ciclo, montar_ciclos, ciclo_da_data, ciclo_atual, verificar_cobertura
│   │   └── categoria.py        # CATEGORIAS_INICIAIS
│   ├── models/lancamento.py
│   ├── schemas/
│   │   ├── categoria.py        # CategoriaOut
│   │   ├── lancamento.py       # LancamentoIn, LancamentoPatch, LancamentoOut
│   │   └── ciclo.py            # CicloOut, SugestaoSalarioOut
│   ├── services/
│   │   ├── categoria.py        # criar_categorias_iniciais, listar, obter_do_usuario
│   │   ├── lancamento.py       # criar, obter, editar, excluir (com cobertura e lock)
│   │   └── ciclo.py            # atual, da_data, lancamentos_do_ciclo, sugestao_salario
│   └── api/routes/
│       ├── categorias.py
│       ├── lancamentos.py
│       └── ciclos.py           # /ciclos/* e /salarios/sugestao
└── tests/
    ├── domain/test_ciclo.py
    └── api/test_categorias.py, test_lancamentos.py, test_ciclos.py
```

**Structure Decision**: segue a estrutura da 002 e do CLAUDE.md. `services/auth.cadastrar`
passa a chamar `criar_categorias_iniciais`.

## Complexity Tracking

Sem violações da constituição a justificar.
