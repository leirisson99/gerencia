---

description: "Tarefas da feature 006 — Recorrências"
---

# Tasks: Recorrências

**Input**: `specs/006-recorrencias/` ([plan.md](plan.md), [spec.md](spec.md),
[contracts/api.md](contracts/api.md))

**Tests**: obrigatórios, escritos antes e vistos falhando.

- **[Story]**: US1 = Cadastrar; US2 = Gerar ao abrir o ciclo; US3 = Confirmar; US4 = Alterar/desativar

## Phase 1: Testes primeiro

- [X] T001 [P] Testes de `data_prevista` (mesmo mês, mês seguinte, dia 31 em fevereiro/abril, bissexto, virada de ano, dia igual ao início) em tests/domain/test_recorrencia.py
- [X] T002 [P] [US1] [US2] [US3] [US4] Testes de API (cenários da spec, validação, isolamento, idempotência) em tests/api/test_recorrencias.py

## Phase 2: Implementação

- [X] T003 `data_prevista` em app/domain/recorrencia.py
- [X] T004 Modelo `Recorrencia` (`valor` BIGINT > 0, `dia` 1–31, `descricao` varchar(200), `tipo` da categoria, `ativa`) e `Lancamento.recorrencia_id` em app/models/recorrencia.py e app/models/lancamento.py
- [X] T005 Migração reversível em alembic/versions/0006_recorrencia.py
- [X] T006 [US1] [US4] Schemas `RecorrenciaIn`, `RecorrenciaPatch`, `RecorrenciaOut`; `LancamentoOut.recorrencia_id` em app/schemas/recorrencia.py e app/schemas/lancamento.py
- [X] T007 [US1] [US2] [US4] `listar`, `criar_recorrencia`, `editar_recorrencia`, `gerar_previstos(db, usuario_id, ciclo, agora)` em app/services/recorrencia.py
- [X] T008 [US2] `criar_lancamento` gera os previstos quando o salário abre o ciclo mais recente em app/services/lancamento.py
- [X] T009 [US1] [US4] Rotas em app/api/routes/recorrencias.py; registrar em app/main.py

## Phase 3: Polish

- [X] T010 Migração ida e volta, `alembic check`, ruff e pytest verdes
- [X] T011 Validação de quickstart.md (coberta pelos testes de API contra PostgreSQL; sem servidor manual)
