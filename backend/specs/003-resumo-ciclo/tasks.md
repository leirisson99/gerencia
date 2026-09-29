---

description: "Tarefas da feature 003 — Resumo do Ciclo"
---

# Tasks: Resumo do Ciclo

**Input**: `specs/003-resumo-ciclo/` ([plan.md](plan.md), [spec.md](spec.md),
[contracts/api.md](contracts/api.md))

**Tests**: obrigatórios (Princípio III), escritos antes e vistos falhando.

- **[Story]**: US1 = Quanto entrou, saiu e sobrou; US2 = Por categoria
- Caminhos relativos a `backend/`

## Phase 1: Testes primeiro

- [X] T001 [P] [US1] Testes de `resumir`: totais, saldo negativo, previsto e `conta_no_saldo = False` fora, ciclo vazio; [US2] somas por categoria fecham com os totais em tests/domain/test_saldo.py
- [X] T002 [P] [US1] [US2] Testes da rota: cenários US1.1–1.5 e US2.1–2.4, só salário, categoria inativa com nome, ciclo aberto, 404 `sem_ciclo`, isolamento, 401 em tests/api/test_resumo.py

## Phase 2: US1 + US2 (P1) 🎯 MVP

- [X] T003 [US1] `Movimento`, `Resumo`, `resumir` para passar T001 em app/domain/saldo.py
- [X] T004 [US2] Schemas `TotalCategoriaOut` e `ResumoCicloOut` em app/schemas/resumo.py
- [X] T005 [US2] `resumo_do_ciclo(db, usuario_id, data)`: lançamentos do ciclo → `resumir` → listas nomeadas e ordenadas (total desc, nome) em app/services/resumo.py
- [X] T006 [US1] Rota `GET /api/v1/ciclos/{data}/resumo` em app/api/routes/ciclos.py

## Phase 3: Polish

- [X] T007 `uv run ruff check . && uv run ruff format --check .` e `uv run pytest` verdes
- [X] T008 Validação manual de quickstart.md
