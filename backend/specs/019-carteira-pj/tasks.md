# Tasks: Carteiras PF e PJ

**Input**: documentos em `specs/019-carteira-pj/`: [plan.md](plan.md), [spec.md](spec.md),
[research.md](research.md), [data-model.md](data-model.md),
[contracts/carteiras.md](contracts/carteiras.md), [quickstart.md](quickstart.md)

**Tests**: obrigatórios (constituição 7.0.0, princípio III). Cada teste é escrito antes e
precisa falhar primeiro.

**Caminhos**: backend relativo a `backend/`; frontend em `../frontend/`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode rodar em paralelo (arquivos diferentes, sem dependência pendente)
- **[Story]**: US1–US5 da spec

---

## Phase 1: Setup

- [X] T001 Atualizar `CLAUDE.md` (pendência da emenda 7.0.0):
  - no glossário, "Carteira: `pf` (a pessoa) ou `pj` (a empresa da pessoa), atributo de
    lançamentos e recorrências; PJ opcional para `prestador` e `clt_prestador`, com ciclo
    sempre pelo mês" e "Retirada: dinheiro da PJ para a PF; gera saída 'Retirada para PF' na
    PJ e entrada 'Pró-labore e lucros' na PF, presas à retirada";
  - no modelo de dados, `usuario.tem_pj`, `lancamento.carteira`, `recorrencia.carteira` e a
    linha da tabela `retirada`;
  - nas regras de cálculo, "Ciclo (carteira PJ): mês do calendário, sem salário" e "Saldo e
    gasto são sempre de uma carteira".

---

## Phase 2: Foundational (bloqueia todas as histórias)

- [X] T002 [P] Em `tests/domain/test_usuario.py` (ou num novo `tests/domain/test_carteira.py`),
  testar:
  - `ciclo_pelo_mes(tipo_renda, carteira="pf")`: `True` para (`prestador`, `pf`) e para
    (`clt`, `clt_prestador` ou `prestador`, `pj`); `False` para (`clt`, `pf`) e
    (`clt_prestador`, `pf`);
  - `pode_ter_pj(tipo)`: só `prestador` e `clt_prestador`;
  - `verificar_pj(tem_pj_novo: bool, tipo_novo: str, tem_dados_pj: bool) -> str | None`:
    - `"tipo_sem_pj"` ao ligar sendo `clt`;
    - `"pj_com_dados"` ao desligar com dados, ou ao trocar para `clt` com dados;
    - `None` nos demais casos.
- [X] T003 [P] Escrever `tests/domain/test_retirada.py` com estes casos:
  - `validar_retirada(valor, data, hoje)` recusa `valor <= 0` (campo `valor`) e `data > hoje`
    (campo `data`), e aceita `data == hoje`;
  - `lados_da_retirada(valor, data)` devolve 2 movimentos, `("pj", "saida")` e
    `("pf", "entrada")`, com o mesmo valor e a mesma data.
- [X] T004 Implementar em `app/domain/usuario.py` a assinatura nova
  `ciclo_pelo_mes(tipo_renda: str, carteira: Carteira = "pf")`, mais `pode_ter_pj` e
  `verificar_pj`, e o tipo `Carteira = Literal["pf", "pj"]` com `CARTEIRA_PADRAO = "pf"`. Criar
  `app/domain/retirada.py` com `validar_retirada` e `lados_da_retirada`. Em
  `app/domain/categoria.py`, criar `NOME_RETIRADA_PJ = "Retirada para PF"`,
  `NOME_PRO_LABORE = "Pró-labore e lucros"` e `CATEGORIAS_PJ` (saída e entrada, `sistema=True`)
  (depende de T002 e T003).
- [X] T005 [P] Nos modelos:
  - `app/models/usuario.py`: `tem_pj: Mapped[bool]` com `server_default=false()`;
  - `app/models/lancamento.py` e `app/models/recorrencia.py`: `carteira: Mapped[str]` com
    `String(2)`, `default="pf"`, `server_default="pf"` e
    `CheckConstraint("carteira IN ('pf', 'pj')", name="carteira")`;
  - em `lancamento`, trocar `Index("ix_lancamento_usuario_data", "usuario_id", "data")` por
    `Index("ix_lancamento_usuario_carteira_data", "usuario_id", "carteira", "data")`.
- [X] T006 [P] Criar `app/models/retirada.py` com a classe `Retirada`:
  - `id` bigint identity;
  - `usuario_id` FK `CASCADE`, com índice;
  - `data: date`;
  - `valor` BigInteger com `CheckConstraint("valor > 0", name="valor_positivo")`;
  - `descricao` `String(200)`, nulo;
  - `lancamento_pj_id` e `lancamento_pf_id`, FK `lancamento.id` `ondelete="RESTRICT"`,
    `unique=True`;
  - `criado_em` timestamptz.
  Exportar em `app/models/__init__.py`. Em `app/models/evento_uso.py`, acrescentar
  `"retirada_feita"`, `"retirada_editada"` e `"retirada_excluida"` ao `TipoEvento`.
- [X] T007 Criar `alembic/versions/0018_carteira_pj.py` (`down_revision="0017"`, com os tipos
  de evento escritos na própria migração, como na 0017). A migração:
  - adiciona `usuario.tem_pj`, `lancamento.carteira` e `recorrencia.carteira`, com os `CHECK`;
  - troca o índice de `lancamento`;
  - cria `retirada`;
  - recria `ck_evento_uso_tipo` com os 30 tipos.
  O downgrade falha com mensagem clara se houver linha com `carteira = 'pj'` ou retirada, e
  senão desfaz tudo. Depois, rodar `uv run alembic upgrade head` e `uv run alembic check`
  (depende de T005 e T006).
- [X] T008 Nos schemas:
  - `Carteira` em `app/schemas/lancamento.py` e `app/schemas/recorrencia.py`: entrada
    `carteira: Carteira = "pf"` em `LancamentoIn` e `RecorrenciaIn`, `carteira: Carteira | None`
    no `LancamentoPatch` (`null` recusado, como os demais campos), e `carteira` em
    `LancamentoOut` e `RecorrenciaOut`;
  - `tem_pj` em `UsuarioOut` e `PerfilIn` (`app/schemas/usuario.py` ou onde estiverem);
  - novo `app/schemas/retirada.py`: `RetiradaIn` (`valor: int > 0`, `data: date`,
    `descricao: str | None`, máximo 200, limpa como as demais), `RetiradaPatch` (todos
    opcionais) e `RetiradaOut` (`id`, `data`, `valor`, `descricao`, `lancamento_pj_id`,
    `lancamento_pf_id`).
- [X] T009 Em `app/services/ciclo.py`, acrescentar o parâmetro `carteira: Carteira = "pf"` a
  `primeira_data_lancamento`, `ciclo_da_data_do_usuario`, `ciclo_atual_do_usuario`,
  `obter_ciclo_atual`, `obter_ciclo_da_data`, `lancamentos_do_ciclo` e `lancamentos_no_ciclo`,
  que passam a filtrar `Lancamento.carteira == carteira` e a usar
  `ciclo_pelo_mes(tipo, carteira)`. `datas_de_salario` e `sugestao_salario` filtram sempre
  `carteira == "pf"`. Criar `exigir_carteira(db, usuario_id, carteira)`, que levanta 409
  `carteira_pj_desligada` se `carteira == "pj"` e `not usuario.tem_pj` (depende de T004 e
  T005).

**Checkpoint**: testes de domínio verdes, migração aplicada e `uv run pytest` inteiro verde,
sem mudança de comportamento.

---

## Phase 3: User Story 1 — ligar a PJ e lançar nela (Priority: P1) 🎯 MVP

**Objetivo**: perfil `tem_pj`, ciclo e saldo PJ, isolamento entre carteiras e cobertura só PF.

**Independent Test**: Carlos liga a PJ e lança + 800000, − 7500 e − 30000 na PJ. O resumo PJ de
outubro tem saldo 762500, e o resumo PF continua com saldo 0.

- [X] T010 [P] [US1] Escrever `tests/api/test_carteira_pj.py` (parte US1), com relógio em
  15/10/2026, cobrindo:
  - ligar a PJ: `prestador` e `clt_prestador` ok, e `GET /me` traz `tem_pj: true`; `clt` → 409
    `tipo_sem_pj`;
  - ligar a PJ cria "Retirada para PF" (saída) e "Pró-labore e lucros" (entrada) com
    `sistema=true`; ligar de novo não duplica; uma categoria existente de mesmo nome e mesmo
    tipo é promovida; com tipo diferente → 409 `categoria_conflitante`;
  - lançar com `carteira: "pj"` sem a PJ ligada → 409 `carteira_pj_desligada`; `GET
    /ciclos/atual?carteira=pj` sem a PJ → 409;
  - o cenário do Carlos (Independent Test) via `/ciclos/2026-10-01/resumo?carteira=pj` e
    `?carteira=pf`;
  - isolamento por rota: com um lançamento PF e um PJ, cada uma das 4 rotas de ciclo, nas duas
    carteiras, traz só o da carteira pedida; sem o parâmetro = PF;
  - `clt_prestador` sem salário: lançar na PJ → 201; lançar na PF → 409 `sem_ciclo`;
    `/ciclos/atual?carteira=pj` responde o mês, sem 404;
  - "Salário" na PJ → 422 com `campos.categoria_id`;
  - lançamento sem `carteira` → `carteira: "pf"` na resposta;
  - mudar a carteira de um lançamento PF para PJ via `PATCH` segue as regras da PJ (aceito para
    `clt_prestador` sem salário, já que o lançamento sai da PF);
  - excluir o único salário de um `clt_prestador` que tem só lançamentos PJ é aceito;
  - limite por categoria: um gasto PJ não conta no aviso de limite da PF;
  - lançamento PJ de outro usuário → 404 em `GET`, `PATCH` e `DELETE`.
- [X] T011 [US1] Em `app/services/categoria.py`, criar `garantir_categorias_pj(db, usuario_id)`,
  idempotente, com a promoção e o 409 de research R5. Em `app/services/perfil.py`, aceitar
  `tem_pj` em `atualizar_perfil`: usar `verificar_pj` (onde `tem_dados_pj` = existe lançamento,
  recorrência ou retirada PJ) e chamar `garantir_categorias_pj` ao ligar, tudo antes do commit
  existente (depende de T010).
- [X] T012 [US1] Em `app/services/lancamento.py`:
  - `criar_lancamento` e `editar_lancamento` leem a carteira (nova ou atual) e chamam
    `exigir_carteira`;
  - recusam "Salário" na PJ (422 `campos.categoria_id`, "Na PJ, use a retirada para levar
    dinheiro à PF.");
  - aplicam a cobertura por salário só quando a carteira final é PF;
  - `menor_data_dos_outros` e `_problema_depois_da_mudanca` passam a filtrar
    `carteira == "pf"`;
  - o lançamento PJ usa `ciclo_pelo_mes(tipo, "pj")` para as regras de data (mesmas do
    `prestador`).
- [X] T013 [P] [US1] Filtrar a carteira em `app/services/resumo.py` (`resumo_do_ciclo(...,
  carteira="pf")`) e em `app/services/limite.py` (`usado_no_ciclo` e `avaliar_aviso` usam a
  carteira do lançamento). Em `app/services/importacao.py`, a cobertura filtra só a PF e as
  linhas importadas ficam `pf`.
- [X] T014 [US1] Em `app/api/routes/ciclos.py`, criar
  `carteira: Annotated[Carteira, Query()] = "pf"` nas 4 rotas, chamando `exigir_carteira` e
  passando a carteira aos services. Em `/ciclos/atual` e `/ciclos/{data}` com `carteira=pj`,
  chamar `garantir_previstos_do_mes(..., carteira="pj")` quando for o mês atual (fica pronto
  em T021).
- [X] T015 [US1] Rodar `uv run pytest tests/api/test_carteira_pj.py` e a suíte inteira, e
  corrigir até ficar verde.

**Checkpoint**: o Carlos já separa PF e PJ; quem não tem PJ não percebe diferença.

---

## Phase 4: User Story 2 — retirada (Priority: P1)

**Objetivo**: CRUD de `/retiradas` com os dois lados presos.

**Independent Test**: retirar 500000 em 25/10 faz o saldo PJ cair 500000 e cria a entrada PF de
500000 em "Pró-labore e lucros".

- [X] T016 [P] [US2] Escrever `tests/api/test_retiradas.py` cobrindo:
  - criar: 201, os dois lados com a mesma data e o mesmo valor, `realizado`,
    `conta_no_saldo=true`, nas categorias e carteiras certas, e a `descricao` nos dois;
  - SC-001 completo (o exemplo do Carlos: PJ 262500, PF 230000);
  - editar valor, data e descrição muda os dois lados;
  - excluir remove a retirada e os dois lados;
  - editar ou excluir um lado por `/lancamentos/{id}` → 409 `lancamento_de_retirada`; mudar a
    carteira de um lado → 409;
  - valor 0 e data futura → 422;
  - sem a PJ → 409 `carteira_pj_desligada`;
  - `clt_prestador` com data antes do primeiro salário → 409 `sem_ciclo`, e nada é gravado;
  - `GET` em lista e por id; a retirada de outro usuário → 404 em `GET`, `PATCH` e `DELETE`;
  - eventos `retirada_feita`, `retirada_editada` e `retirada_excluida`, um por ação.
- [X] T017 [US2] Criar `app/services/retirada.py` com `criar_retirada`, `listar_retiradas`,
  `obter_retirada`, `editar_retirada` e `excluir_retirada`. Cada uma:
  - chama `travar_escritas` e `exigir_carteira(..., "pj")`, e usa `validar_retirada` e
    `lados_da_retirada`;
  - busca as categorias de sistema por nome e verifica a cobertura do lado PF com a mesma
    função do lançamento PF;
  - grava tudo numa transação, com `registrar(...)` do evento antes do commit.
- [X] T018 [US2] Em `app/services/lancamento.py`, criar `_e_lado_de_retirada(db, id)` e
  recusar com 409 `lancamento_de_retirada` ("Este lançamento é de uma retirada: altere pela
  retirada.") em `editar_lancamento` e `excluir_lancamento`, no padrão de
  `_e_deposito_de_cartela`.
- [X] T019 [US2] Criar `app/api/routes/retiradas.py` (prefixo `/api/v1/retiradas`, 5 rotas do
  contrato, `AutenticadoDep`) e registrá-lo em `app/main.py`.

---

## Phase 5: User Story 3 — recorrências da empresa (Priority: P2)

**Independent Test**: "DAS" 7500, dia 20, na PJ. Abrir a PJ de outubro duas vezes gera um único
previsto em 20/10, e nada na PF.

- [X] T020 [P] [US3] Em `tests/api/test_carteira_pj.py` (parte US3), testar:
  - criar recorrência PJ com e sem a PJ ligada;
  - recorrência sem carteira = `pf`;
  - a geração idempotente na PJ ao abrir o mês, duas vezes;
  - o salário PF de um `clt_prestador` não gera o previsto PJ;
  - `GET /recorrencias?carteira=pj` filtra;
  - criar recorrência PJ no meio do mês gera o previsto do mês corrente da PJ.
- [X] T021 [US3] Em `app/services/recorrencia.py`:
  - `gerar_previstos(..., carteira="pf")` usa só as recorrências da carteira e grava os
    previstos com ela;
  - `garantir_previstos_do_mes(db, usuario_id, hoje, agora, carteira="pf")` roda sempre na PJ
    e, na PF, só se `ciclo_pelo_mes(tipo, "pf")`;
  - `criar_recorrencia` chama `exigir_carteira` e gera no ciclo atual da carteira dela;
  - `listar_recorrencias` aceita o filtro.
  Ajustar os chamadores (lançamento e importação ao abrir ciclo PF passam `"pf"`). Em
  `app/api/routes/recorrencias.py`, criar `?carteira=` no `GET`.

---

## Phase 6: User Story 4 — lembretes (Priority: P3)

- [X] T022 [P] [US4] Em `tests/api/test_lembretes.py`, criar um teste em que um previsto PJ e um
  PF para amanhã aparecem os dois, com `carteira` `pj` e `pf`, e o lembrete livre tem `pf`.
- [X] T023 [US4] Em `app/schemas/lembrete.py` (`ItemLembrete`) e `app/services/lembrete.py`,
  incluir `carteira` (do lançamento; `pf` para livres). A janela e a regra não mudam.

---

## Phase 7: User Story 5 — desligar a PJ e troca de tipo (Priority: P3)

- [X] T024 [P] [US5] Em `tests/api/test_carteira_pj.py` (parte US5), testar:
  - desligar sem dados PJ: ok, e o seletor some (`tem_pj: false`);
  - desligar com lançamento, recorrência ou retirada PJ → 409 `pj_com_dados`;
  - trocar para `clt` com dados PJ → 409; sem dados → ok, e `tem_pj` vira `false`;
  - `prestador` → `clt_prestador` com dados PJ e sem salário: a cobertura ignora a PJ, e a
    troca só é recusada se houver lançamento PF fora de ciclo.
- [X] T025 [US5] Em `app/services/perfil.py`, `_checar_troca_tipo_renda` e
  `_tem_salario_irregular` passam a olhar só a PF. Na troca para `clt`, aplicar `verificar_pj`
  e desligar `tem_pj` quando não houver dados.

---

## Phase 8: Administrador

- [X] T026 [P] Em `tests/api/test_admin_atividade.py`, testar que `contagens.retiradas` conta
  as retiradas e que os lados contam em `lancamentos_gerados`. Ajustar
  `test_detalhe_traz_contagens_por_funcionalidade`, que ganha `"retiradas": 0`.
- [X] T027 Em `app/schemas/admin.py`, criar `ContagensContaOut.retiradas`. Em
  `app/services/admin.py` (`_contagens`), contar `Retirada` do usuário, e incluir em `gerado`
  `Lancamento.id.in_(lancamento_pj_id ∪ lancamento_pf_id das retiradas)`. Em
  `../frontend/features/admin/rotulos-atividade.ts`, criar os 3 rótulos de evento e a contagem
  "Retiradas da PJ".

---

## Phase 9: Frontend

- [X] T028 [P] Em `../frontend/lib/api/types.ts`:
  - `Carteira = "pf" | "pj"`;
  - `carteira` em `Lancamento`, `Recorrencia` e no item de lembrete;
  - `tem_pj` em `Usuario`;
  - o tipo `Retirada`.
  Criar `../frontend/lib/carteira.ts` (server-only): `obterCarteira()` lê o cookie `carteira` e
  devolve `"pj"` só se o usuário tiver `tem_pj`, senão `"pf"`.
- [X] T029 Em `../frontend/lib/api/server.ts`, passar `?carteira=` em `obterCiclo`,
  `listarLancamentosDoCiclo`, o resumo, `listarLancamentosDoPeriodo` (calendário) e
  `listarRecorrencias`, lendo de `obterCarteira()`. Criar `../frontend/lib/api/retiradas.ts`
  com `criarRetirada`, `editarRetirada` e `excluirRetirada` (depende de T028).
- [X] T030 Criar `../frontend/components/layout/seletor-carteira.tsx` (client): grupo segmentado
  "PF | PJ" com `aria-pressed`, que grava o cookie (`path=/`, 1 ano) e chama
  `router.refresh()`. Ele só aparece com `usuario.tem_pj`. Incluí-lo no
  `../frontend/components/layout/app-shell.tsx` (topo no desktop e no celular), recebendo a
  carteira atual do servidor.
- [X] T031 [P] Em `../frontend/features/lancamentos/form-lancamento.tsx` e
  `../frontend/features/recorrencias/dialog-recorrencia.tsx`, enviar `carteira` (a aberta) ao
  criar e esconder "Salário" da lista de categorias na PJ. Na lista de lançamentos, os lados
  de retirada mostram "Retirada" e o menu leva à edição da retirada (sem editar nem excluir
  direto).
- [X] T032 Criar `../frontend/features/retiradas/dialog-retirada.tsx`: botão "Retirar para PF"
  visível na visão PJ (início e lançamentos), com os campos valor (`CampoValor`), data (padrão
  hoje) e descrição opcional. O mesmo diálogo serve para editar e excluir a partir do lado da
  retirada. Os erros da API aparecem no formulário (`aplicarErroApi`).
- [X] T033 [P] Em `../frontend/features/perfil/form-perfil.tsx`, criar o interruptor "Tenho
  CNPJ (carteira PJ)", visível para `prestador` e `clt_prestador`, com uma explicação curta:
  "Separa o dinheiro da empresa do seu. A PJ conta pelo mês do calendário." Os erros
  `pj_com_dados` e `categoria_conflitante` aparecem com a mensagem da API.
- [X] T034 [P] Em `../frontend/features/lembretes/lista-lembretes.tsx`, criar o selo "PJ" nos
  itens da PJ, visível só para quem tem a PJ.

---

## Phase 10: Polish & Cross-Cutting

- [X] T035 Revisar no backend todo `select(Lancamento` e `select(Recorrencia` (busca no código)
  e confirmar que cada consulta de ciclo, saldo, limite ou cobertura filtra a carteira, ou
  justificar no código por que soma as duas (lembretes, admin).
- [X] T036 Rodar `uv run pytest`, `uv run ruff check .` e `uv run ruff format .` no backend, e
  `npm run lint`, `npx tsc --noEmit` e `npm run build` no frontend. Corrigir o que falhar.
- [X] T037 [P] Atualizar o Status da spec e marcar esta lista.
- [ ] T038 Validar os cenários de [quickstart.md](quickstart.md) no navegador.

---

## Dependencies & Execution Order

- **Setup (T001)**: independente.
- **Foundational (T002–T009)**: bloqueia tudo. T002 e T003 → T004; T005 e T006 → T007; T004 e
  T005 → T009; T008 depois de T005.
- **US1 (T010–T015)**: depende da Foundational. É o MVP.
- **US2 (T016–T019)**: depende de US1 (categorias de sistema, `exigir_carteira`, cobertura
  PF).
- **US3 (T020–T021)**: depende de US1; T014 usa `garantir_previstos_do_mes` com carteira de
  T021 (até lá, a rota só não gera previstos PJ).
- **US4 (T022–T023)** e **US5 (T024–T025)**: dependem de US1; independentes entre si.
- **Admin (T026–T027)**: depende de US2.
- **Frontend (T028–T034)**: T028 → T029 → T030 e T032; T031, T033 e T034 em paralelo depois de
  T029. Pode começar quando a API de US1 estiver pronta.
- **Polish (T035–T038)**: no fim.

## Parallel Example

```text
# Foundational:
T002 | T003 | T005 | T006
# Depois de US1:
T016 (testes de retirada) | T020 (testes de recorrência) | T022 | T024
# Frontend:
T031 | T033 | T034
```

## Implementation Strategy

1. **MVP**: Foundational + US1. O Carlos já separa a PJ da PF, lançando à mão nos dois lados.
2. **Incremento 2**: US2 (retirada), que fecha o exemplo de referência (SC-001).
3. **Incremento 3**: US3, US4, US5 e admin.
4. **Frontend** junto de cada incremento, ou no fim, se preferir validar a API primeiro.
5. Um commit por fase, em Conventional Commits:
   - `feat: carteira PJ no perfil e no ciclo`;
   - `feat: retirada da PJ para a PF`;
   - `feat: recorrências por carteira`;
   - `feat: carteira nos lembretes`;
   - `feat: seletor PF/PJ no app`.
