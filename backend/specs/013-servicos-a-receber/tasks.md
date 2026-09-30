# Tasks: Serviços a Receber

**Input**: [plan.md](plan.md), [spec.md](spec.md), [data-model.md](data-model.md),
[contracts/api.md](contracts/api.md), [research.md](research.md)

**Tests**: obrigatórios (Constituição, Princípio III): domínio com teste antes; endpoints com
teste de API contra PostgreSQL.

## Phase 1: Setup

- [X] T001 Confirmar a base verde: `uv run pytest -q` e `uv run ruff check .` em `backend/`

## Phase 2: Foundational (bloqueia todas as histórias)

- [X] T002 [P] Testes de domínio (vermelho) em tests/domain/test_servico.py: `situacao(status, data_prevista, hoje)` → `recebido` para realizado (qualquer data), `atrasado` para previsto com data prevista ontem, `a_receber` para hoje e amanhã; `descricao_do_lancamento(cliente, descricao)` → cliente sozinho, `"cliente — descrição"`, corte em 200 caracteres
- [X] T003 [P] Testes de domínio (vermelho) em tests/domain/test_usuario.py: `tem_servicos(tipo)` True para `prestador` e `clt_prestador`, False para `clt`
- [X] T004 Implementar `tem_servicos` em app/domain/usuario.py e `SituacaoServico`, `situacao`, `descricao_do_lancamento` em app/domain/servico.py
- [X] T005 Migração alembic/versions/0013_servico.py: tabela `servico` com `id BIGINT IDENTITY` PK, `usuario_id` FK `usuario.id` `ON DELETE CASCADE` com índice, `categoria_id` FK `categoria.id` `ON DELETE RESTRICT`, `cliente VARCHAR(120) NOT NULL`, `descricao VARCHAR(200) NULL`, `valor BIGINT NOT NULL` com `CHECK (valor > 0)`, `data_prevista DATE NOT NULL`, `lancamento_id BIGINT NOT NULL UNIQUE` FK `lancamento.id` `ON DELETE RESTRICT`, `criado_em TIMESTAMPTZ NOT NULL`; `downgrade` com `drop_table`
- [X] T006 Modelo `Servico` em app/models/servico.py (espelhando a migração) e registro em app/models/__init__.py
- [X] T007 `column_property` `servico_id` em app/models/lancamento.py (como `cartela_id`) e `servico_id: int | None` em `LancamentoOut` (app/schemas/lancamento.py)
- [X] T008 Schemas em app/schemas/servico.py: `ServicoIn` (cliente ≤ 120 obrigatório via `limpar_texto`, descricao ≤ 200 opcional via `limpar_descricao`, `valor: Valor`, `data_prevista: date`, `categoria_id: int`, `extra="forbid"`), `ServicoPatch` (tudo opcional; `null` só em descricao), `RecebimentoIn` (`data: date`, `valor: Valor | None = None`), `ServicoOut` e `SituacaoServico` Literal
- [X] T009 Dependência `ComServicosDep` em app/api/deps.py: depois de `autenticacao`, 403 `perfil_sem_servicos` se `not tem_servicos(usuario.tipo_renda)`

## Phase 3: User Story 1 — Registrar um serviço (P1)

**Goal**: criar serviço com entrada prevista. **Independent Test**: prestador registra serviço e
vê o previsto no ciclo.

- [X] T010 [US1] Testes de API (vermelho) em tests/api/test_servicos.py (fixtures de prestador, clt_prestador e clt; relógio em 15/10/2026): criar → 201 `a_receber` e previsto ligado (`servico_id`, valor, categoria, data, descrição gerada); validações 422 (cliente vazio/longo, valor 0/negativo/não inteiro); categoria de saída, inativa ou "Salário" → 422 `campos.categoria_id`; categoria de outro usuário → 404; data passada → `atrasado`; clt → 403 `perfil_sem_servicos` em todas as rotas; clt_prestador sem salário → 409 `salario_necessario`
- [X] T011 [US1] Em app/services/servico.py: `criar_servico` (trava escritas, valida categoria com `obter_categoria_ativa` + tipo entrada + não salário, `verificar_novos_lancamentos(data_prevista)`, cria lançamento previsto + serviço, commit) e `servico_out(servico, hoje)` montando `ServicoOut` com situação e dados de recebimento
- [X] T012 [US1] Rotas `POST /api/v1/servicos` e `GET /api/v1/servicos/{id}` em app/api/routes/servicos.py (com `ComServicosDep`) e `include_router` em app/main.py

## Phase 4: User Story 2 — Marcar como recebido (P1)

**Goal**: receber e desfazer. **Independent Test**: receber muda o saldo; desfazer volta.

- [X] T013 [US2] Testes de API (vermelho) em tests/api/test_servicos.py: receber sem valor (realizado, data, valor combinado, saldo sobe) e com valor diferente (serviço mantém o combinado); data futura → 422 `campos.data`; receber de novo → 409 `servico_recebido`; desfazer → previsto na data prevista com o valor do serviço, situação volta, saldo volta; desfazer não recebido → 409 `servico_nao_recebido`; clt_prestador recebendo antes do primeiro salário → 409 `antes_do_primeiro_ciclo`
- [X] T014 [US2] `receber_servico` e `desfazer_recebimento` em app/services/servico.py (trava, cobertura com `verificar_novos_lancamentos`, commit)
- [X] T015 [US2] Rotas `POST` e `DELETE /api/v1/servicos/{id}/recebimento` em app/api/routes/servicos.py

## Phase 5: User Story 3 — Ver o que tenho a receber (P1)

**Goal**: listagem com filtro. **Independent Test**: três situações, filtro por atrasado.

- [X] T016 [US3] Testes de API (vermelho) em tests/api/test_servicos.py: lista ordenada por data prevista; filtro por cada situação; previsto para hoje é `a_receber`; recebido mostra `data_recebimento` e `valor_recebido`; situação inválida → 422; outro usuário não vê e recebe 404 em todas as rotas do serviço (test_isolamento.py cobre só dados de conta; o isolamento financeiro fica no arquivo de cada feature)
- [X] T017 [US3] `listar_servicos(db, usuario_id, hoje, situacao)` em app/services/servico.py e rota `GET /api/v1/servicos` com `situacao` opcional em app/api/routes/servicos.py

## Phase 6: User Story 4 — Corrigir ou excluir (P2)

**Goal**: editar/excluir com o previsto acompanhando; lançamento travado. **Independent Test**:
editar valor e data e conferir o previsto; excluir e ver sumir; tentar editar o lançamento.

- [X] T018 [US4] Testes de API (vermelho) em tests/api/test_servicos.py: editar valor/data/cliente/descrição/categoria sincroniza o previsto; `descricao: null` remove; excluir → 204 e previsto some; editar/excluir recebido → 409 `servico_recebido`; `PATCH /lancamentos` do lançamento de serviço com valor, status, categoria ou data → 422 e com descrição → 200; `DELETE /lancamentos` → 409 `lancamento_de_servico`
- [X] T019 [US4] `editar_servico` e `excluir_servico` em app/services/servico.py
- [X] T020 [US4] Rotas `PATCH` e `DELETE /api/v1/servicos/{id}` em app/api/routes/servicos.py
- [X] T021 [US4] Trava em app/services/lancamento.py: em `editar_lancamento`, lançamento com `servico_id` e dono com `tem_servicos` recusa mudança de valor, status, categoria_id ou data (422, "Altere pelo serviço."); em `excluir_lancamento`, 409 `lancamento_de_servico`

## Phase 7: User Story 5 — Deixar de prestar serviço (P3)

**Goal**: troca para clt só sem pendentes. **Independent Test**: pendente bloqueia; recebido
não.

- [X] T022 [US5] Testes de domínio (vermelho) em tests/domain/test_ciclo.py: `verificar_troca_tipo_renda(..., servicos_pendentes=True)` para `clt` → `SERVICOS_PENDENTES` (com precedência), para `clt_prestador`/`prestador` → sem esse problema
- [X] T023 [US5] Testes de API (vermelho) em tests/api/test_servicos.py: clt_prestador com pendente → clt 409 `servicos_pendentes`; só recebidos → aceito e lançamento deixa de ser travado; prestador com pendente → clt_prestador aceito (com salário cobrindo)
- [X] T024 [US5] `SERVICOS_PENDENTES` e parâmetro `servicos_pendentes: bool = False` em app/domain/ciclo.py; app/services/perfil.py consulta serviços não recebidos e responde 409 `servicos_pendentes`

## Phase 8: Polish

- [X] T025 `uv run ruff check . && uv run ruff format .`; `uv run pytest`; `uv run alembic downgrade -1 && uv run alembic upgrade head`
- [X] T026 Revisar o OpenAPI contra contracts/api.md; atualizar CLAUDE.md se algo divergir

## Dependencies

- Phase 2 bloqueia tudo. US1 antes de US2–US4 (todas precisam de um serviço criado). US3 e
  US4 independem entre si depois de US2. US5 depende de US1 e US2.

## Parallel Example

```text
T002 test_servico.py ‖ T003 test_usuario.py
```

## Implementation Strategy

MVP = Phase 2 + US1 + US2 + US3 (registrar, receber, listar). Depois US4 (correções e trava) e
US5 (troca). Commits: `test:` → `feat:` por fase.
