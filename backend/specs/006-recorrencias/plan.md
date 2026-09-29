# Implementation Plan: Recorrências

**Branch**: `006-recorrencias` | **Date**: 2026-09-29 | **Spec**: [spec.md](spec.md)

## Summary

Tabela `recorrencia` e coluna `lancamento.recorrencia_id` (migração `0006`). Rotas
`GET/POST /api/v1/recorrencias` e `PATCH /api/v1/recorrencias/{id}`. A data do previsto é a regra
pura `data_prevista(dia, inicio_ciclo)` em `domain/recorrencia.py`. A geração
(`gerar_previstos`) roda quando `criar_lancamento` grava um salário que abre o ciclo mais
recente e quando uma recorrência é criada com ciclo aberto; é idempotente por ciclo.

## Technical Context

**Language/Version**: Python 3.14 · **Dependencies**: as mesmas

**Storage**: PostgreSQL 17 — `recorrencia`, `lancamento.recorrencia_id` (FK RESTRICT) e índice
`(recorrencia_id, data)` ([data-model.md](data-model.md))

**Testing**: `tests/domain/test_recorrencia.py`, `tests/api/test_recorrencias.py`

**Project Type**: web service; escopo só do backend

## Constitution Check

| Princípio | Verificação | Status |
| --- | --- | --- |
| I. Integridade | Valor `StrictInt` > 0 em centavos; previsto não entra no saldo (regra da 003). | ✅ |
| II. Ciclo | Geração quando o ciclo abre; um previsto por recorrência por ciclo; salário não é recorrência. | ✅ |
| III. Teste primeiro | `data_prevista` pura (fim de mês, virada de ano) testada antes; geração testada pela API. | ✅ |
| IV. Contratos | `RecorrenciaIn/Patch/Out` tipados; `LancamentoOut.recorrencia_id`. | ✅ |
| V. Isolamento | Recorrência e categoria de outro usuário → 404 (teste). | ✅ |
| VI. Escopo | Só o P0 (cadastrar, gerar, confirmar, alterar/desativar); sem exclusão. | ✅ |

**Resultado**: sem violações.

## Project Structure

```text
backend/
├── alembic/versions/0006_recorrencia.py
├── app/domain/recorrencia.py      # data_prevista
├── app/models/recorrencia.py      # + Lancamento.recorrencia_id
├── app/schemas/recorrencia.py
├── app/services/recorrencia.py    # criar, editar, listar, gerar_previstos
├── app/services/lancamento.py     # criar salário que abre ciclo → gerar_previstos
├── app/api/routes/recorrencias.py
└── tests/domain/test_recorrencia.py, tests/api/test_recorrencias.py
```

## Decisões

- **Quando gerar**: ao criar um salário cuja data é maior que a de todos os salários anteriores
  (abre o ciclo mais recente); ao criar uma recorrência com ciclo aberto. Editar salários não
  gera.
- **Idempotência**: não gera se já existe lançamento da recorrência com data dentro do ciclo.
- **Previsto**: `status = previsto`, valor/categoria/tipo/descrição da recorrência,
  `recorrencia_id` preenchido. Passa pela mesma cobertura (a data é ≥ início do ciclo).
- **Confirmar**: `PATCH /lancamentos/{id} {"status": "realizado", ...}` (feature 001).

## Complexity Tracking

Sem violações.
