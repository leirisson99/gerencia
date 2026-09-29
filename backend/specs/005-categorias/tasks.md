---

description: "Tarefas da feature 005 — Categorias Editáveis"
---

# Tasks: Categorias Editáveis

**Input**: `specs/005-categorias/` ([plan.md](plan.md), [spec.md](spec.md),
[contracts/api.md](contracts/api.md))

**Tests**: obrigatórios, escritos antes e vistos falhando.

- **[Story]**: US1 = Criar; US2 = Renomear; US3 = Desativar e reativar

## Phase 1: Testes primeiro

- [X] T001 [P] Testes de `edicao_permitida` (sistema não renomeia nem desativa; comum pode) em tests/domain/test_categoria.py
- [X] T002 [P] [US1] [US2] [US3] Testes de API: criar, nome repetido (maiúsculas/espaços), validação, renomear com lançamentos e resumo, "Salário" protegida, desativar/reativar, lista com inativas, lançamento em inativa, tipo não editável, isolamento em tests/api/test_categorias.py

## Phase 2: Implementação

- [X] T003 Migração `0005` com índice único `uq_categoria_usuario_nome` em `(usuario_id, lower(nome))` em alembic/versions/0005_categoria_nome_unico.py; índice no modelo em app/models/categoria.py
- [X] T004 `edicao_permitida` em app/domain/categoria.py
- [X] T005 [US1] [US2] Schemas `CategoriaIn` (nome ≤ 60, tipo `entrada | saida`), `CategoriaPatch` (nome, ativa, sem null), `CategoriaOut.ativa` em app/schemas/categoria.py
- [X] T006 [US1] [US2] [US3] `listar_categorias(..., incluir_inativas)`, `criar_categoria`, `editar_categoria` em app/services/categoria.py
- [X] T007 Rotas `GET` (com `incluir_inativas`), `POST`, `PATCH /categorias/{id}` em app/api/routes/categorias.py

## Phase 3: Polish

- [X] T008 Migração ida e volta, `alembic check`, ruff e pytest verdes
- [X] T009 Validação de quickstart.md (coberta pelos testes de API contra PostgreSQL; sem servidor manual)
