---

description: "Tarefas da feature 009 — Limite por Categoria (backend + frontend)"
---

# Tasks: Limite por Categoria

**Input**: `specs/009-limite-categoria/` ([plan.md](plan.md), [spec.md](spec.md),
[research.md](research.md), [data-model.md](data-model.md), [contracts/api.md](contracts/api.md))

**Tests**: obrigatórios (constituição, Princípio III), escritos antes e vistos falhando.

- **[Story]**: US1 = Definir limite; US2 = Ver uso no resumo; US3 = Aviso ao lançar
- Caminhos do backend relativos a `backend/`; do frontend, a `frontend/`.

## Phase 1: Setup

- [X] T001 Migração reversível `categoria.limite BIGINT NULL` com `CHECK (limite > 0)` (nome `limite_positivo`) em alembic/versions/0009_limite_categoria.py; campo `limite: Mapped[int | None]` em app/models/categoria.py

## Phase 2: Foundational (regra pura)

- [X] T002 [P] Testes de `situacao(usado, limite)` (fronteiras 79,99%, 80%, 100%, 100,01%; usado 0; limite 1 centavo), `piorou(antes, depois)` (ok<atencao<estourado; igual não piora; melhora não piora) e `limite_permitido(tipo)` (só "saida") em tests/domain/test_limite.py
- [X] T003 Implementar `situacao` ("ok" se `usado*100 < limite*80`; "atencao" se `usado <= limite`; senão "estourado"), `piorou` e `limite_permitido` em app/domain/limite.py

**Checkpoint**: `uv run pytest tests/domain/test_limite.py` verde.

## Phase 3: User Story 1 — Definir o limite (P1) 🎯 MVP

**Independent test**: definir limite em "Lazer", ver em `GET /categorias`; remover; limite em entrada recusado.

- [X] T004 [US1] Testes de API (definir, mudar, remover com `null`, ausente não muda, criar já com limite, entrada → 422 `campos.limite`, zero/negativo/fração → 422, categoria de outro usuário → 404, "Poupança" aceita limite) em tests/api/test_limite.py; `limite` nos corpos esperados de tests/api/test_categorias.py
- [X] T005 [US1] `limite` em `CategoriaIn` (opcional, `Valor`), `CategoriaPatch` (`Valor | None`, null permitido) e `CategoriaOut` em app/schemas/categoria.py
- [X] T006 [US1] `criar_categoria`/`editar_categoria` validam com `limite_permitido` (422 `validacao`, `campos.limite`) e aplicam `limite` só se estiver em `model_fields_set` em app/services/categoria.py
- [X] T007 [P] [US1] Frontend: `Categoria.limite`, `CategoriaIn.limite`, `CategoriaPatch.limite` (`number | null`) em lib/api/types.ts
- [X] T008 [US1] Frontend: campo opcional "Limite por ciclo" (`CampoValor`, só saída, com "Sem limite") no dialog e "limite R$ X" nas linhas de saída em features/categorias/dialog-categoria.tsx e features/categorias/lista-categorias.tsx; permitir limite (não nome) nas categorias do sistema de saída

## Phase 4: User Story 2 — Ver o uso no resumo (P1)

**Independent test**: limite de R$ 300 em Lazer; gastos de R$ 100, R$ 240, R$ 300,01 → ok, atenção, estourado; previsto não conta; sem gasto → total 0.

- [X] T009 [US2] Testes de API do resumo (cenários 1–7 da US2; categoria desativada com limite e sem gasto não aparece; parcela no cartão não conta; somas fecham) em tests/api/test_limite.py; `limite`/`situacao` nos corpos esperados de tests/api/test_resumo.py
- [X] T010 [US2] `limite: int | None` e `situacao: Literal["ok","atencao","estourado"] | None` em `TotalCategoriaOut` em app/schemas/resumo.py
- [X] T011 [US2] Resumo inclui limite e situação (via `domain/limite.situacao`) e categorias ativas de saída com limite e sem gasto (total 0, depois das com gasto) em app/services/resumo.py
- [X] T012 [P] [US2] Frontend: `TotalCategoria.limite`/`situacao` em lib/api/types.ts
- [X] T013 [US2] Frontend: medidor usado ÷ limite com "R$ X de R$ Y" e situação em ícone + texto ("Atenção" em cor de texto; "Estourado" em vermelho) em features/resumo/totais-por-categoria.tsx (carregar a skill dataviz e validar cores antes)

## Phase 5: User Story 3 — Aviso ao lançar (P2)

**Independent test**: limite R$ 300, R$ 200 gastos; lançar R$ 50 → aviso "atencao"; +R$ 10 → sem aviso; +R$ 50 → "estourado"; todos 201.

- [X] T014 [US3] Testes de API (cenários 1–8 da US3; excluir e reduzir não avisam; lançamento que não conta no saldo não avisa; entrada não avisa) em tests/api/test_limite.py
- [X] T015 [US3] `AvisoLimiteOut {categoria_id, nome, usado, limite, situacao}` e `LancamentoComAvisoOut(LancamentoOut)` com `aviso_limite: AvisoLimiteOut | None` em app/schemas/lancamento.py
- [X] T016 [US3] `usado_no_ciclo(db, usuario_id, categoria_id, data)` (reusa `obter_ciclo_da_data`, `lancamentos_no_ciclo`, `domain/saldo.resumir`) e `avaliar_aviso(antes, depois, categoria)` em app/services/limite.py
- [X] T017 [US3] `criar_lancamento`/`editar_lancamento` medem o usado da categoria de destino no ciclo da nova data antes da mudança e depois do `flush`, e devolvem `(lancamento, aviso)` em app/services/lancamento.py
- [X] T018 [US3] `POST`/`PATCH` respondem `LancamentoComAvisoOut` em app/api/routes/lancamentos.py
- [X] T019 [P] [US3] Frontend: `AvisoLimite` e retorno de `criarLancamento`/`editarLancamento` como `Lancamento & { aviso_limite }` em lib/api/types.ts e lib/api/lancamentos.ts
- [X] T020 [US3] Frontend: `toast.warning` "Lazer em atenção: R$ 250,00 de R$ 300,00" ao salvar e ao confirmar previsto em features/lancamentos/dialog-lancamento.tsx e features/lancamentos/confirmar-previsto.tsx

## Phase 6: Polish

- [X] T021 Migração ida e volta, `alembic check`, `uv run ruff check . && uv run ruff format --check .`, `uv run pytest` verdes
- [X] T022 Frontend: `npx next typegen`, `npx tsc --noEmit`, `npm run lint` verdes
- [X] T023 Validar quickstart.md de ponta a ponta pelo Next (`localhost:3000/api/v1`), com a API reiniciada

## Dependencies

- T001 → tudo; T002 → T003 → US1/US2/US3.
- US1 (T004–T008) antes de US2 e US3 (precisam de limite definido).
- US2 e US3 independentes entre si depois de US1.
- Em cada história: testes → schemas → services → rotas → frontend.

## Parallel Examples

- Phase 2: T002 (teste de domínio) em paralelo com o preparo de T004.
- US1: T007 (tipos do front) em paralelo com T005–T006.
- US2: T012 em paralelo com T010–T011. US3: T019 em paralelo com T015–T018.

## Implementation Strategy

MVP = Phases 1–3 (limite definido e visível). Depois US2 (resumo e medidor), que entrega o valor
principal, e por fim US3 (aviso). Cada fase termina com testes verdes e checagem ponta a ponta.
