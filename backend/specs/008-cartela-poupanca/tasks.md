---

description: "Tarefas da feature 008 — Cartela de Poupança"
---

# Tasks: Cartela de Poupança

**Input**: `specs/008-cartela-poupanca/` ([plan.md](plan.md), [spec.md](spec.md),
[contracts/api.md](contracts/api.md))

**Tests**: obrigatórios, escritos antes e vistos falhando.

- **[Story]**: US1 = Criar; US2 = Marcar/desmarcar; US3 = Progresso

## Phase 1: Testes primeiro

- [X] T001 [P] Testes de `gerar_casas` (exemplos do briefing, divisão exata, soma = meta, meta < base) e `progresso` em tests/domain/test_cartela.py
- [X] T002 [P] [US1] [US2] [US3] Testes de API em tests/api/test_cartelas.py
- [X] T003 Ajustar testes de categorias iniciais para incluir "Poupança" (sistema) e a proteção de categorias do sistema em tests/api/test_categorias.py, tests/api/test_cadastro.py, tests/domain/test_categoria.py

## Phase 2: Implementação

- [X] T004 `gerar_casas`, `progresso` em app/domain/cartela.py; "Poupança" em `CATEGORIAS_INICIAIS` e proteção por `sistema` em app/domain/categoria.py
- [X] T005 Modelos `Cartela`, `Casa` em app/models/cartela.py
- [X] T006 Migração reversível (tabelas + "Poupança" para usuários existentes) em alembic/versions/0008_cartela.py
- [X] T007 [US1] [US3] Schemas em app/schemas/cartela.py
- [X] T008 [US1] [US2] [US3] `criar_cartela`, `listar`, `obter`, `depositar`, `desfazer_deposito` em app/services/cartela.py
- [X] T009 [US2] Proteção do lançamento de depósito em app/services/lancamento.py; proteção por `sistema` em app/services/categoria.py
- [X] T010 Rotas em app/api/routes/cartelas.py; registrar em app/main.py

## Phase 3: Polish

- [X] T011 Migração ida e volta, `alembic check`, ruff e pytest verdes
- [X] T012 Validação de quickstart.md (coberta pelos testes de API contra PostgreSQL; sem servidor manual)
