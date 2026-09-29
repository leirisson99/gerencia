---

description: "Tarefas da feature 007 — Dívidas com Parcelas"
---

# Tasks: Dívidas com Parcelas

**Input**: `specs/007-dividas/` ([plan.md](plan.md), [spec.md](spec.md),
[contracts/api.md](contracts/api.md))

**Tests**: obrigatórios, escritos antes e vistos falhando.

- **[Story]**: US1 = Cadastrar e gerar parcelas; US2 = Marcar paga/recebida; US3 = Acompanhar

## Phase 1: Testes primeiro

- [X] T001 [P] Testes de `dividir` (resto na última, soma = total, 1 parcela, total = n), `datas_das_parcelas` (fim de mês, virada de ano, 1ª no próprio início) e `situacao` em tests/domain/test_parcelas.py
- [X] T002 [P] [US1] [US2] [US3] Testes de API (cenários da spec, validação, cartão, cobertura, parcela não exclui nem troca categoria, isolamento) em tests/api/test_dividas.py

## Phase 2: Implementação

- [X] T003 `dividir`, `datas_das_parcelas`, `situacao` em app/domain/parcelas.py
- [X] T004 Modelo `Divida` e `Lancamento.divida_id`/`parcela_num` em app/models/divida.py e app/models/lancamento.py
- [X] T005 Migração reversível em alembic/versions/0007_divida.py
- [X] T006 [US1] [US3] Schemas `DividaIn`, `DividaOut`; `LancamentoOut.divida_id`, `parcela_num` em app/schemas/divida.py e app/schemas/lancamento.py
- [X] T007 [US1] [US3] `criar_divida`, `listar_dividas`, `obter_divida` em app/services/divida.py
- [X] T008 [US2] Cobertura pública e bloqueio de exclusão/troca de categoria de parcela em app/services/lancamento.py
- [X] T009 Rotas em app/api/routes/dividas.py; registrar em app/main.py

## Phase 3: Polish

- [X] T010 Migração ida e volta, `alembic check`, ruff e pytest verdes
- [X] T011 Validação de quickstart.md (coberta pelos testes de API contra PostgreSQL; sem servidor manual)
