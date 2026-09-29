---

description: "Tarefas da feature 001 — Ciclo Aberto pelo Salário"
---

# Tasks: Ciclo Aberto pelo Salário

**Input**: Design documents from `specs/001-ciclo-salario/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/api.md](contracts/api.md), [quickstart.md](quickstart.md)

**Tests**: obrigatórios (Princípio III). Todos os testes foram escritos antes da implementação e
confirmados falhando.

## Format: `[ID] [P?] [Story] Description`

- **[Story]**: US1 = Lançar o salário, US2 = Bloqueio antes do primeiro salário,
  US3 = Ver e navegar entre ciclos, US4 = Corrigir ou excluir um salário
- Caminhos relativos a `backend/`

---

## Phase 1: Testes primeiro

- [X] T001 [P] Testes das regras puras de ciclo e cobertura (montar, da data, atual, mesmo dia, virada de ano, SC-002, cobertura) em tests/domain/test_ciclo.py
- [X] T002 [P] Fixture `criar_conta` (usuário logado com categorias iniciais) em tests/conftest.py
- [X] T003 [P] Testes de `GET /categorias` (8 iniciais em ordem, inativas fora, isolamento, 401) em tests/api/test_categorias.py
- [X] T004 [P] Testes de lançamentos: US1, US2, US4, validação de `valor` (`StrictInt`, `> 0`, `≤ 99.999.999.999`), `descricao` (≤ 200, vazio → null), categoria inexistente/de outro usuário → 404, inativa → 422, isolamento em tests/api/test_lancamentos.py
- [X] T005 [P] Testes de ciclos: US3 (atual, por data com vizinhos, navegação, antes do primeiro → 404 `sem_ciclo`, virada de ano), lançamentos do ciclo, sugestão do salário, isolamento em tests/api/test_ciclos.py
- [X] T006 Ajustar o teste do cadastro para esperar as 8 categorias iniciais em tests/api/test_cadastro.py

---

## Phase 2: Foundational

- [X] T007 [P] `CATEGORIAS_INICIAIS` ("Salário" entrada sistema; "Renda extra" entrada; "Moradia", "Alimentação", "Transporte", "Saúde", "Lazer", "Outros" saídas) em app/domain/categoria.py
- [X] T008 [P] Modelo `Lancamento`: `usuario_id` FK CASCADE; `categoria_id` FK RESTRICT; `data` date; `valor` BIGINT `CHECK (valor > 0)`; `tipo` varchar(7) CHECK `entrada | saida`; `descricao` varchar(200) null; `status` varchar(9) CHECK `previsto | realizado` default `realizado`; `conta_no_saldo` default true; `criado_em`, `atualizado_em`; índices `(usuario_id, data)` e `(usuario_id, categoria_id, data)` em app/models/lancamento.py
- [X] T009 Migração com a tabela `lancamento` e a inserção das categorias iniciais para usuários existentes (lista literal), `downgrade` reversível, em alembic/versions/0003_lancamento_categorias_iniciais.py
- [X] T010 `criar_categorias_iniciais(db, usuario_id)`, listagem ordenada e `obter_categoria_do_usuario` (404 se não existe ou é de outro) em app/services/categoria.py; `cadastrar` passa a usá-la em app/services/auth.py
- [X] T011 Regras puras `Ciclo`, `montar_ciclos`, `ciclo_da_data`, `ciclo_atual`, `verificar_cobertura` para passar T001 em app/domain/ciclo.py

---

## Phase 3: US1 + US2 — Lançar o salário e bloqueio (P1) 🎯 MVP

- [X] T012 [US1] Schemas `CategoriaOut`, `LancamentoIn`, `LancamentoPatch`, `LancamentoOut` (com `abre_ciclo` derivado) em app/schemas/categoria.py e app/schemas/lancamento.py
- [X] T013 [US1] Serviço `criar_lancamento` e `obter_lancamento`: lock do usuário, categoria do usuário e ativa, `tipo` da categoria, salário só `realizado` e com data ≤ hoje (SP), verificação de cobertura (`salario_necessario`, `antes_do_primeiro_ciclo`) em app/services/lancamento.py
- [X] T014 [US1] Rotas `GET /categorias`, `POST /lancamentos`, `GET /lancamentos/{id}` em app/api/routes/categorias.py e app/api/routes/lancamentos.py; registrar os routers em app/main.py

---

## Phase 4: US3 — Ver e navegar entre ciclos (P2)

- [X] T015 [US3] Schemas `CicloOut` e `SugestaoSalarioOut` em app/schemas/ciclo.py
- [X] T016 [US3] Serviço `datas_de_salario`, `ciclo_atual_do_usuario`, `ciclo_da_data_do_usuario` (404 `sem_ciclo`), `lancamentos_do_ciclo`, `sugestao_salario` em app/services/ciclo.py
- [X] T017 [US3] Rotas `GET /ciclos/atual`, `GET /ciclos/{data}`, `GET /ciclos/{data}/lancamentos`, `GET /salarios/sugestao` em app/api/routes/ciclos.py

---

## Phase 5: US4 — Corrigir ou excluir um salário (P2)

- [X] T018 [US4] `editar_lancamento` (PATCH parcial, `descricao: null` remove, recategorizar troca `tipo`) e `excluir_lancamento`, com cobertura sobre o estado resultante (`lancamentos_sem_ciclo` quando a mudança é num salário) em app/services/lancamento.py
- [X] T019 [US4] Rotas `PATCH /lancamentos/{id}` e `DELETE /lancamentos/{id}` em app/api/routes/lancamentos.py

---

## Phase 6: Polish

- [X] T020 `uv run alembic downgrade -1 && uv run alembic upgrade head` e `alembic check` sem diferenças
- [X] T021 `uv run ruff check . && uv run ruff format --check .` e `uv run pytest` verdes
- [X] T022 Validação manual de quickstart.md contra a API rodando

---

## Dependencies & Execution Order

- Phase 1 (testes) já concluída; Phase 2 bloqueia as demais.
- US1+US2 juntas: o bloqueio é a mesma regra de cobertura usada ao criar.
- US3 depende só da Phase 2 (os testes de ciclo lançam salários via US1).
- US4 depende de US1 (edita e exclui lançamentos criados por ela).
