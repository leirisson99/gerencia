# Tasks: Tipo de Renda e Ciclo Mensal do Prestador

**Input**: [plan.md](plan.md), [spec.md](spec.md), [data-model.md](data-model.md),
[contracts/api.md](contracts/api.md), [research.md](research.md)

**Tests**: obrigatórios (Constituição, Princípio III): regra de domínio nasce com teste escrito
antes; endpoints com teste de API contra PostgreSQL.

## Phase 1: Setup

- [X] T001 Confirmar a base verde antes de mudar: `uv run pytest` e `uv run ruff check .` em `backend/`

## Phase 2: Foundational (bloqueia todas as histórias)

- [X] T002 [P] Testes de domínio (vermelho) para `TIPOS_RENDA`, `TIPO_CLT`, `TIPO_PRESTADOR`, `TIPO_CLT_PRESTADOR` e `ciclo_pelo_mes(tipo)` (só `prestador` → True) em tests/domain/test_usuario.py
- [X] T003 [P] Testes de domínio (vermelho) para `ciclo_mensal(data, hoje, primeira_data)` em tests/domain/test_ciclo.py: fevereiro de 28 e 29 dias, meses de 30 e 31 dias, dia 1, último dia, virada de ano (anterior de janeiro = 01/12 do ano anterior; próximo de dezembro = 01/01), mês atual (`aberto` e `mes_atual` True, sem próximo), mês futuro (fechado, sem próximo), sem anterior quando `primeira_data` é None ou ≥ início do mês; e `Ciclo(...)` antigo continua com `aberto = fim is None`
- [X] T004 Implementar em app/domain/usuario.py as constantes de tipo de renda e `ciclo_pelo_mes`
- [X] T005 Implementar em app/domain/ciclo.py: campo `mes_atual: bool = False` em `Ciclo`, `aberto` = `fim is None or mes_atual`, e `ciclo_mensal(data, hoje, primeira_data)` conforme data-model.md
- [X] T006 Migração alembic/versions/0012_tipo_renda.py: `usuario.tipo_renda VARCHAR(13) NOT NULL DEFAULT 'clt'` com `CHECK (tipo_renda IN ('clt','prestador','clt_prestador'))`, `downgrade` remove coluna e check
- [X] T007 Adicionar `tipo_renda` (String(13), `server_default "clt"`, `CheckConstraint` nomeado `tipo_renda`) em app/models/usuario.py
- [X] T008 Em app/models/lancamento.py: `column_property` `tipo_renda_usuario` (subconsulta escalar de `Usuario.tipo_renda`, como `cartela_id`) e `abre_ciclo` falso quando o tipo for `prestador`
- [X] T009 Em app/services/ciclo.py: `travar_escritas` passa a devolver o `tipo_renda` (mesmo `SELECT ... FOR UPDATE`); novas `tipo_renda_do_usuario`, `primeira_data_lancamento`, `ciclo_da_data_do_usuario(db, usuario_id, data, hoje)` e `ciclo_atual_do_usuario(db, usuario_id, hoje)`; `obter_ciclo_atual`, `obter_ciclo_da_data` e `lancamentos_do_ciclo` recebem `hoje` e usam as novas funções
- [X] T010 Em app/api/routes/ciclos.py passar `relogio.hoje_sp()` às funções de ciclo (e ao resumo)
- [X] T011 Em app/services/limite.py `usado_no_ciclo` recebe `hoje` e usa `ciclo_da_data_do_usuario`; atualizar as chamadas em app/services/lancamento.py
- [X] T012 Em app/services/resumo.py `resumo_do_ciclo` recebe `hoje` e usa `obter_ciclo_da_data` com ele
- [X] T013 Rodar a suíte completa: o fluxo CLT não pode mudar (SC-002)

**Checkpoint**: ciclo escolhido por tipo de renda num único ponto; nenhum teste antigo alterado.

## Phase 3: User Story 1 — Informar como recebo (P1)

**Goal**: tipo de renda no cadastro e no perfil. **Independent Test**: cadastrar com e sem
`tipo_renda` e conferir no `/me`.

- [X] T014 [P] [US1] Testes de API (vermelho) em tests/api/test_cadastro.py: cadastro com `prestador`, sem tipo (→ `clt`), com valor inválido (422 `campos.tipo_renda`); `GET /me` traz `tipo_renda`
- [X] T015 [P] [US1] Testes de API (vermelho) em tests/api/test_perfil.py: `PATCH /me` `clt` → `clt_prestador` aceito; `tipo_renda: null` recusado (422)
- [X] T016 [US1] Em app/schemas/usuario.py: `TipoRenda = Literal["clt","prestador","clt_prestador"]`; `CadastroIn.tipo_renda: TipoRenda = "clt"`; `PerfilIn.tipo_renda: TipoRenda | None` recusando null; `UsuarioOut.tipo_renda`
- [X] T017 [US1] Em app/services/auth.py gravar `tipo_renda=dados.tipo_renda` no cadastro

## Phase 4: User Story 2 — Prestador controla o mês sem salário (P1)

**Goal**: prestador lança sem salário; ciclo = mês. **Independent Test**: conta prestador nova
lança gasto e entrada e consulta ciclo e resumo.

- [X] T018 [P] [US2] Testes de API (vermelho) em tests/api/test_prestador.py (fixture de cliente prestador): gasto sem salário aceito; `GET /ciclos/atual` = mês de hoje aberto, nunca 404; resumo com saldo do mês; ciclo de 10/02/2028 = 01/02–29/02; "Salário" previsto e futuro aceito, `abre_ciclo` false e não muda o ciclo; anterior/próximo conforme lançamentos; dívida, depósito em cartela e importação (prévia sem `antes_do_primeiro_ciclo`, confirmação com "Salário" futuro) sem pedir salário; isolamento: outro usuário `clt` continua exigindo salário
- [X] T019 [US2] Em app/services/lancamento.py: `_problema_depois_da_mudanca` devolve None quando `ciclo_pelo_mes` do tipo do usuário; `_validar_salario` só roda com ciclo pelo salário (usar o tipo devolvido por `travar_escritas` em criar e editar); `abre_ciclo` falso para prestador em `criar_lancamento` e `editar_lancamento`
- [X] T020 [US2] Em app/services/importacao.py: `previa` usa `primeiro_salario=None` para prestador; `confirmar` pula `_validar_linhas` de salário futuro, `cobertura_do_lote` e `novo_ciclo_aberto` para prestador

## Phase 5: User Story 3 — Fixos e limites no mês (P2)

**Goal**: previstos de recorrência por mês e limite medido no mês. **Independent Test**:
recorrência no dia 10 aparece uma vez no mês; limite de setembro não conta em outubro.

- [X] T021 [US3] Testes de API (vermelho) em tests/api/test_prestador.py: recorrência criada gera previsto no mês; `GET /ciclos/atual` repetido não duplica; mês novo (relógio avançado) gera o previsto ao consultar ciclo atual ou resumo; recorrência no dia 31 cai em 28/02; limite de Lazer com gasto em setembro não avisa em 01/10
- [X] T022 [US3] Em app/services/recorrencia.py: `garantir_previstos_do_mes(db, usuario_id, hoje, agora)` (trava escritas; só para prestador; `gerar_previstos` no mês atual; commit); `criar_recorrencia` recebe `hoje` e usa `ciclo_atual_do_usuario`
- [X] T023 [US3] Chamar `garantir_previstos_do_mes` em `GET /ciclos/atual` e `GET /ciclos/{data}/resumo` (app/api/routes/ciclos.py) e em `criar_lancamento` (gerar no mês atual para prestador, app/services/lancamento.py); passar `hoje` em app/api/routes/recorrencias.py

## Phase 6: User Story 4 — Trocar o tipo sem perder dados (P2)

**Goal**: troca de tipo segura. **Independent Test**: `clt` → `prestador` → `clt` com e sem
salário.

- [X] T024 [P] [US4] Testes de domínio (vermelho) em tests/domain/test_ciclo.py para `verificar_troca_tipo_renda(atual, novo, datas_salario, menor_data_outros, salario_irregular)`: mesmo tipo, `clt`↔`clt_prestador`, `clt*`→`prestador` aceitos; `prestador`→`clt*` com salário irregular → `SALARIO_INVALIDO` (precedência), sem salário com lançamentos → `LANCAMENTOS_SEM_CICLO`, lançamento antes do primeiro salário → `LANCAMENTOS_SEM_CICLO`, sem lançamento nenhum → aceito
- [X] T025 [P] [US4] Testes de API (vermelho) em tests/api/test_prestador.py (usa os helpers de lançamento do prestador): cenários 1–6 da história 4 (409 `lancamentos_sem_ciclo`, 409 `salario_invalido`, aceites) e ciclo atual muda de salário para mês após a troca
- [X] T026 [US4] Implementar `ProblemaTroca` e `verificar_troca_tipo_renda` em app/domain/ciclo.py
- [X] T027 [US4] Em app/services/perfil.py: com `tipo_renda` enviado e diferente, `travar_escritas`, coletar `datas_de_salario`, `menor_data_dos_outros` e se existe "Salário" previsto ou com data > hoje; chamar o domínio e levantar 409 `lancamentos_sem_ciclo` ou `salario_invalido` com as mensagens de contracts/api.md

## Phase 7: Polish

- [X] T028 `uv run ruff check . && uv run ruff format .`; `uv run pytest`; `uv run alembic downgrade -1 && uv run alembic upgrade head`
- [X] T029 Revisar o OpenAPI (`/docs`) contra contracts/api.md e seguir quickstart.md

## Dependencies

- Phase 2 bloqueia tudo. US1 (tipo no cadastro) facilita os testes de US2–US4, que usam a
  fixture de prestador; US2 antes de US3 (mesmo arquivo de teste e de service). US4 depende só
  da Phase 2 e de US1.
- [P] em testes: arquivos diferentes, escritos antes da implementação da fase.

## Parallel Example

```text
T002 test_usuario.py  ‖  T003 test_ciclo.py
T014 test_cadastro.py ‖  T015 test_perfil.py
T024 test_ciclo.py    ‖  T025 test_perfil.py
```

## Implementation Strategy

MVP = Phase 2 + US1 + US2 (prestador já usa o sistema). Depois US3 (recorrência e limite) e US4
(troca segura). Commits pequenos: `test:` → `feat:` por fase.
