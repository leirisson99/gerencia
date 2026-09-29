---

description: "Tarefas da feature 004 — Painel do Administrador"
---

# Tasks: Painel do Administrador

**Input**: `specs/004-painel-admin/` ([plan.md](plan.md), [spec.md](spec.md),
[contracts/api.md](contracts/api.md))

**Tests**: obrigatórios, escritos antes e vistos falhando.

- **[Story]**: US1 = Criar o administrador; US2 = Listar e buscar contas; US3 = Resetar senha
- Caminhos relativos a `backend/`

## Phase 1: Testes primeiro

- [X] T001 [P] [US3] Testes de `gerar_senha_temporaria`: 12 caracteres, passa em `validar_senha`, só letras e dígitos, chamadas diferentes geram senhas diferentes em tests/domain/test_senha_temporaria.py
- [X] T002 [P] [US1] Testes de `criar_administrador`: cria com papel admin e troca obrigatória, sem categorias; segundo admin recusado; e-mail repetido recusado; dados inválidos recusados em tests/services/test_criar_admin.py
- [X] T003 [P] [US2] [US3] Testes das rotas: acesso negado a usuário comum, 401, admin com troca pendente → 403; listagem só com `id,nome,email,criado_em`, ordem, busca, sem o admin; reset derruba sessões, senha antiga falha, temporária entra com troca obrigatória, auditoria gravada, 404 para inexistente e para o admin; usuário comum não reseta em tests/api/test_admin.py

## Phase 2: Foundational

- [X] T004 Modelo `AcaoAdmin` (`admin_id` FK CASCADE, `acao` varchar(30) CHECK `reset_senha`, `usuario_alvo_id` FK CASCADE indexado, `ocorrida_em` timestamptz) em app/models/acao_admin.py; índice único parcial `uq_usuario_admin_unico` em app/models/usuario.py
- [X] T005 Migração reversível em alembic/versions/0004_acao_admin.py
- [X] T006 `gerar_senha_temporaria()` para passar T001 em app/services/senha.py

## Phase 3: US1 — Criar o administrador (P1)

- [X] T007 [US1] `criar_administrador(db, dados, agora) -> (Usuario, senha)` com as validações do cadastro, erro se já houver admin ou e-mail repetido, em app/services/admin.py
- [X] T008 [US1] Comando `criar-admin` (argparse; imprime a senha; código 1 em erro) em app/cli.py

## Phase 4: US2 + US3 — Listar e resetar (P1)

- [X] T009 [US2] Dependência `AdministradorDep` (403 `acesso_negado`) em app/api/deps.py
- [X] T010 [US2] Schemas `UsuarioAdminOut`, `SenhaTemporariaOut` em app/schemas/admin.py
- [X] T011 [US2] `listar_usuarios(db, busca)` e [US3] `resetar_senha(db, admin, usuario_id, agora)` (senha gerada, sessões encerradas, troca obrigatória, auditoria na mesma transação) em app/services/admin.py
- [X] T012 [US2] [US3] Rotas `GET /api/v1/admin/usuarios` e `POST /api/v1/admin/usuarios/{id}/reset-senha` em app/api/routes/admin.py; registrar em app/main.py

## Phase 5: Polish

- [X] T013 Atualizar referências "feature 003" (admin) para 004 em specs/002-cadastro-login/spec.md
- [X] T014 Migração ida e volta, `alembic check`, ruff e pytest verdes
- [X] T015 Validação manual de quickstart.md
