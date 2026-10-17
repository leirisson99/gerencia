# Tasks: Contas compartilhadas

**Input**: documentos em `specs/020-conta-compartilhada/`: [plan.md](plan.md), [spec.md](spec.md),
[research.md](research.md), [data-model.md](data-model.md),
[contracts/contas-compartilhadas.md](contracts/contas-compartilhadas.md),
[quickstart.md](quickstart.md)

**Tests**: obrigatórios (constituição 8.1.0, princípio III). Cada teste é escrito antes e
precisa falhar primeiro.

**Caminhos**: backend relativo a `backend/`; frontend em `../frontend/`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode rodar em paralelo (arquivos diferentes, sem dependência pendente)
- **[Story]**: US1 (cadastrar e dividir), US2 (aceitar convite), US3 (cobrança mensal e
  lançamentos), US4 (pagamento da cota)

---

## Phase 1: Setup (governança)

- [X] T001 Emenda da constituição (8.0.0 e 8.1.0) em `.specify/memory/constitution.md`: feita via
  `/speckit-constitution`.
- [X] T002 Atualizar `CLAUDE.md`: glossário (Conta compartilhada, Participante, Cobrança, Cota),
  modelo de dados (4 tabelas), regras de cálculo (cota própria no saldo, soma das cotas ==
  total, divisão só entre aceitos, status da cota derivado do lançamento) e a regra de
  isolamento com a exceção.

---

## Phase 2: Foundational (bloqueia todas as histórias)

- [X] T003 [P] Teste primeiro em `tests/domain/test_conta_compartilhada.py`: `ratear` por
  `modo`. `igual` com `@pytest.mark.parametrize` de (total, n) = (60000, 6), (10000, 3), (200000,
  4), (1, 2), (10000, 1): soma == total e resto na última cota; `percentual` em bps com soma
  10000 e resto na última; `fixo` somando o total (dono incluído); erros para percentual ≠ 10000 e
  fixos ≠ total (com a diferença), n = 0 e n > 20. Também `status_da_cota(lancamento_status, confirmado_em)` →
  `pendente` / `informado` / `confirmado` e `convite_expirado`.
- [X] T004 Em `app/domain/conta_compartilhada.py`: `ratear(total, modo, participantes)`
  (reutiliza `dividir()` de `app/domain/parcelas.py`), `validar_divisao(...)`,
  `status_da_cota(...)`, `convite_expirado(convidado_em, agora)` (30 dias),
  `data_da_cota(competencia, dia)` (ajusta 29 a 31 ao último dia, como `no_mes` em
  `app/domain/recorrencia.py`). `MAX_PARTICIPANTES = 20`. Faz T003 passar.
- [X] T005 Em `app/models/conta_compartilhada.py`, criar os 4 modelos exatamente como em
  `data-model.md`: `modo IN ('igual','percentual','fixo')`, `dia_vencimento BETWEEN 1 AND 31`,
  `valor_fixo > 0` quando não nulo, `status` do participante em (`pendente`, `aceito`,
  `recusado`, `removido`, `saiu`), `UNIQUE (conta_id, competencia)`,
  `UNIQUE (cobranca_id, participante_id)`, UNIQUEs parciais `(conta_id, usuario_id)` e
  `(conta_id, email_convite)`, índice parcial `(participante_id) WHERE lancamento_id IS NULL`.
  `cota_cobranca` tem `confirmado_em` e **não** tem coluna de status; `lancamento_id` é FK
  RESTRICT. Importar em `app/models/__init__.py`.
- [X] T006 Em `app/models/evento_uso.py`, somar a `TipoEvento`: `conta_compartilhada_criada`,
  `convite_aceito`, `convite_recusado`, `cobranca_gerada`, `cota_confirmada`.
- [X] T007 Migração `alembic/versions/0019_conta_compartilhada.py` (`down_revision="0018"`):
  cria as 4 tabelas e recria o `CHECK` de `evento_uso` (padrão `_check_tipos` da 0018). O
  `downgrade` apaga as tabelas e restaura o `CHECK`, recusando apagar se houver cobranças (como
  a 0018 faz com a PJ). Validar `alembic upgrade head`, `downgrade -1`, `upgrade head`.
- [X] T008 [P] Em `app/schemas/conta_compartilhada.py`: `ContaIn`, `ContaPatch`, `ConviteIn`,
  `CobrancaIn`, `AceiteIn`, `ContaDonoOut` (e-mails e valor de cada cota, status derivado),
  `ContaParticipanteOut` (`qtd_pessoas` = aceitos, `qtd_convidados_pendentes`, `minha_cota`,
  `outros: [{nome, status}]`, sem e-mail nem valor alheio), `ConviteOut` (`id`,
  `descricao_conta`, `nome_do_dono`, `convidado_em`). `Modo` e `StatusCota` como `Literal`.
- [X] T009 Em `app/services/conta_compartilhada.py`, o ponto único de acesso
  `conta_visivel(db, conta_id, usuario_id)`: dono ou participante `aceito`; senão `ErroApi(404,
  "nao_encontrado", ...)`. Também `conta_do_dono(...)`, que responde 403 `somente_dono` para
  participante aceito e 404 para quem não participa.
- [X] T010 [P] Registrar `contas_compartilhadas` em `app/main.py` (`include_router` com prefixo
  `/api/v1/contas-compartilhadas`) e criar `app/api/routes/contas_compartilhadas.py` com o
  `APIRouter`. **Regra do arquivo**: rotas estáticas (`/convites`, `/cotas/...`) sempre antes das
  com `/{id}`.

**Checkpoint**: domínio testado e migração aplicada; nenhuma rota exposta ainda.

---

## Phase 3: User Story 1 - Cadastrar a conta e dividir (P1) MVP

**Goal**: o dono cria a conta, define o modo e vê total, número de pessoas (aceitas) e cotas.

**Independent Test**: Ana cria "Aluguel" (valor fixo R$ 2.000, igual), convida 3 pessoas que
aceitam; a API devolve total 200000, `qtd_pessoas = 4`, cota 50000 cada.

- [X] T011 [P] [US1] Em `tests/api/test_contas_compartilhadas.py`, testar `POST /` e `GET /`:
  conta criada com o dono como participante `aceito`; `modo` inválido → 422; 21º participante
  → 409 `limite_participantes`; `GET /{id}` do dono traz total, `qtd_pessoas`,
  `qtd_convidados_pendentes` e cotas; convidados pendentes não entram na `qtd_pessoas`.
- [X] T012 [US1] Em `app/services/conta_compartilhada.py`: `criar_conta` (trava a conta,
  categoria do dono validada como em `_categoria_de_recorrencia`, dono vira participante
  `eh_dono`), `editar_conta` (não muda cobranças já geradas), `convidar` (e-mail normalizado em
  minúsculas, resposta idêntica exista conta ou não, 20 máximo incluindo pendentes),
  `editar_valor_participante`, `remover_participante`, `detalhe_do_dono`. Registra `conta_compartilhada_criada`.
- [X] T013 [US1] Em `app/api/routes/contas_compartilhadas.py`: `POST /`, `GET /`, `GET /{id}`
  (escolhe a visão por papel), `PATCH /{id}`, `POST /{id}/participantes`,
  `PATCH /{id}/participantes/{participante_id}` (valor, inclusive o do dono) e
  `DELETE /{id}/participantes/{participante_id}`.
- [X] T014 [P] [US1] Frontend: `../frontend/lib/api/contas-compartilhadas.ts`, tipos em
  `../frontend/lib/api/types.ts` e `../frontend/features/contas-compartilhadas/dialog-conta.tsx`
  (descrição, categoria, modo, dia, valor fixo opcional, e-mails dos convidados), seguindo
  `features/dividas/dialog-divida.tsx`. Ler `node_modules/next/dist/docs/` antes
  (`../frontend/AGENTS.md`).
- [X] T015 [US1] Frontend: `../frontend/app/(app)/contas-compartilhadas/page.tsx` e
  `[id]/page.tsx` com cartão mostrando **total, número de pessoas (aceitas) e quantos convidados
  faltam aceitar**, e a lista de participantes; item no menu em
  `../frontend/components/layout/app-sidebar.tsx` e `barra-inferior.tsx`; ocultar menu e páginas
  na carteira PJ.

---

## Phase 4: User Story 2 - Aceitar o convite (P1)

**Goal**: o convidado vê o convite (nome do dono, descrição, data), escolhe a categoria e aceita
ou recusa; antes disso a conta responde 404.

**Independent Test**: Bia aceita o convite e passa a ver a conta; um terceiro e Bia antes do
aceite recebem 404 na conta.

- [ ] T016 [P] [US2] Em `tests/api/test_contas_compartilhadas.py` e `tests/api/test_isolamento.py`:
  convite pendente, recusado, removido, expirado (30 dias com `RelogioFixo`) e participante
  `saiu` → 404 na conta; `GET /convites` mostra `descricao_conta`, `nome_do_dono` e data, sem
  valor nem e-mail; participante aceito tentando `PATCH`, convidar ou cobrar → 403
  `somente_dono`; `GET /{id}` do participante traz `outros` só com nome e status; resposta de
  `POST /{id}/participantes` idêntica para e-mail com e sem conta; cadastro de um e-mail
  convidado vincula o convite pendente.
- [ ] T017 [US2] Em `app/services/conta_compartilhada.py`: `convites_do_usuario` (por e-mail do
  usuário, só não expirados), `aceitar` (define `usuario_id` e `categoria_id`, valida a
  categoria, 409 `convite_expirado` após 30 dias, registra `convite_aceito`), `recusar`
  (`convite_recusado`), `sair`, `visao_do_participante`.
- [ ] T018 [US2] Em `app/services/auth.py` (`cadastrar`, linha ~43): ao criar o usuário, vincular
  `participante_conta.usuario_id` aos convites pendentes e não expirados do e-mail. Sem mudar o
  comportamento de cadastro quando não há convite.
- [ ] T019 [US2] Rotas `GET /convites`, `POST /convites/{id}/aceitar`, `POST .../recusar` (todas
  declaradas **antes** das rotas com `{id}`) e `POST /{id}/sair` em
  `app/api/routes/contas_compartilhadas.py`.
- [ ] T020 [P] [US2] Frontend: `../frontend/features/contas-compartilhadas/convites.tsx` (lista de
  convites pendentes no topo da página, com nome do dono e descrição, e escolha de categoria ao
  aceitar) e a visão do participante em `[id]/page.tsx` (total, pessoas, minha cota e `outros` só
  com nome e status).

---

## Phase 5: User Story 3 - Cobrança mensal e lançamentos (P1)

**Goal**: gerar a cobrança do mês e fazer cada participante receber o previsto da própria cota,
protegido contra exclusão e alteração.

**Independent Test**: Ana informa R$ 600 de energia com 6 aceitos; cada um tem cota de R$ 100 e
um previsto de R$ 100 no próprio ciclo; só esses R$ 100 contam no saldo e no gasto por categoria
quando realizado.

- [ ] T021 [P] [US3] Em `tests/api/test_contas_compartilhadas.py`: `POST /{id}/cobrancas` gera
  cotas que somam o total (6, 4 e 3 aceitos); 6 convidados e 3 aceitos divide por 3; segunda
  chamada na mesma competência → 409 `cobranca_ja_gerada`; quem aceita depois e quem sai não
  alteram a cobrança já gerada; percentual ≠ 100% ou fixos > total entre os aceitos → 422;
  conta variável sem cobrança do mês mostra `falta_informar_total` ao dono.
- [ ] T022 [P] [US3] Em `tests/api/test_contas_compartilhadas.py`: conta com `valor_fixo` gera a
  cobrança do mês a partir do dia de vencimento, na leitura de ciclo de **qualquer** participante
  aceito, sem duplicar nem gerar antes; o dono pode gerar antes pelo `POST /{id}/cobrancas`.
  Materialização: leitura de `GET /api/v1/ciclos/atual` cria 1 lançamento previsto da própria
  cota (`conta_no_saldo=True`, `carteira=pf` mesmo com PJ ligada, categoria dele, data =
  vencimento) e uma segunda leitura não duplica; CLT sem ciclo cobrindo a data deixa a cota sem
  lançamento até haver salário; quem saiu ou foi removido ainda recebe o lançamento de cobrança
  já gerada; leitura de um usuário nunca cria lançamento em outro; saldo e gasto por categoria
  só contam a cota própria depois de realizado.
- [ ] T023 [P] [US3] Em `tests/api/test_lancamentos.py` (ou no arquivo de testes do módulo):
  `DELETE` e `PATCH` de `valor` ou `data` do lançamento de uma cota → 409
  `lancamento_de_cota`, e o mesmo para `carteira`, `conta_no_saldo` e `tipo`; `PATCH` de
  `status`, categoria e descrição → permitido; lançamento comum
  continua igual.
- [ ] T024 [US3] Em `app/services/conta_compartilhada.py`: `gerar_cobranca` (trava a conta,
  `ratear` entre participantes `aceito`, 422 com a diferença se percentual ≠ 10000 ou fixos ≠
  total, grava `cobranca_mensal` e `cota_cobranca`, registra `cobranca_gerada`);
  `garantir_cobrancas_fixas(db, usuario_id, hoje)` (contas com `valor_fixo` da competência
  corrente, dos quais o usuário é participante aceito, só a partir do dia de vencimento,
  idempotente e tolerante a conflito simultâneo com `ON CONFLICT DO NOTHING`);
  `materializar_cotas(db, usuario_id, hoje, agora)` idempotente, que considera as cotas do
  usuário independentemente do status atual do participante e cria o previsto só se a data
  cair num ciclo existente do usuário na carteira PF.
- [ ] T025 [US3] Em `app/services/ciclo.py` e `app/api/routes/ciclos.py`: chamar
  `garantir_cobrancas_fixas` e `materializar_cotas` antes de montar as leituras de ciclo (mesmo
  ponto de `garantir_previstos_do_mes`, `routes/ciclos.py` linhas 34 e 65). Sem nada pendente,
  nenhuma escrita nem mudança na resposta; as suítes de ciclo e lançamentos seguem verdes.
- [ ] T026 [US3] Em `app/services/lancamento.py` (excluir em ~`:329`, editar valor e data):
  (inclui `carteira`, `conta_no_saldo` e `tipo`) consultar se existe
  `cota_cobranca.lancamento_id = :id` e, se existir, responder
  `ErroApi(409, "lancamento_de_cota", ...)`; sem coluna nova em `lancamento`. Faz T023 passar.
- [ ] T027 [US3] Rota `POST /{id}/cobrancas` em `app/api/routes/contas_compartilhadas.py`
  (`competencia`, `valor_total`; só o dono) e `falta_informar_total` no `GET /` e `GET /{id}`.
- [ ] T028 [P] [US3] Frontend: `../frontend/features/contas-compartilhadas/dialog-cobranca.tsx`
  (informar o total do mês de água ou luz), aviso "falta informar o total de [mês]" para o dono
  e exibição de total, pessoas e minha cota por mês em `[id]/page.tsx`. Mostrar o lançamento da
  cota com valor e data travados em `features/lancamentos/*`.

---

## Phase 6: User Story 4 - Pagamento da cota (P2)

**Goal**: o titular "paga" e "cancela" realizando e desfazendo o próprio lançamento; o dono
confirma sem tocar no saldo de ninguém.

**Independent Test**: Bia realiza o lançamento (cota "informado"); Ana confirma ("confirmado");
Bia volta o lançamento para previsto (cota "pendente", confirmação invalidada).

- [ ] T029 [P] [US4] Em `tests/api/test_contas_compartilhadas.py`: status derivado da cota
  (`pendente` com previsto, `informado` com realizado, `confirmado` com `confirmado_em` e
  realizado); `POST /cotas/{id}/confirmar` do dono em cota informada; participante tentando
  confirmar → 403 `somente_dono`; confirmar sem lançamento realizado → 409 `cota_nao_informada`;
  `POST .../desfazer-confirmacao`; cancelar (lançamento volta a previsto) leva a `pendente`;
  confirmar e desfazer não alteram nenhum lançamento; confirmar cota de outra conta → 404.
- [ ] T030 [US4] Em `app/services/conta_compartilhada.py`: `confirmar_cota` e
  `desfazer_confirmacao` (só gravam `confirmado_em`; registra `cota_confirmada`) e o cálculo do
  status derivado nas visões do dono e do participante (usa `status_da_cota`).
- [ ] T031 [US4] Rotas `POST /cotas/{cota_id}/confirmar` e `POST /cotas/{cota_id}/desfazer-confirmacao`
  em `app/api/routes/contas_compartilhadas.py` (antes das rotas com `{id}`).
- [ ] T032 [P] [US4] Frontend: botão "Confirmar" (dono) e status por pessoa em
  `../frontend/features/contas-compartilhadas/`; "Paguei" e "Cancelar" no lançamento da cota
  chamam a rota de lançamento existente.

---

## Phase 7: Polish & cross-cutting

- [ ] T033 [P] Em `app/services/admin.py` (`:194-205` e `:267-283`): contar contas
  compartilhadas e participações aceitas por usuário e no global, sem nomes, e-mails ou valores;
  teste em `tests/api/test_admin.py` conferindo que o payload não traz nenhum desses campos.
- [ ] T034 [P] Em `tests/api/test_isolamento.py`: um usuário sem relação com a conta recebe 404 em
  todas as rotas do módulo; `GET /{id}` do participante não contém e-mail nem valor de terceiros.
- [ ] T035 Regressão: `uv run pytest` completo, `uv run ruff check .`, `uv run ruff format
  --check .`; revisar o OpenAPI gerado (princípio IV); no frontend `npm run lint`, `npm run
  build` e `npx tsc --noEmit`.
- [ ] T036 Roteiro manual de `quickstart.md` com dois usuários; marcar o status da spec como
  Implementada.

---

## Dependencies & Execution Order

- Fase 1: T002 antes de qualquer código (T001 já feita).
- Fase 2: T003 → T004; T005 → T006 → T007; T008 e T010 em paralelo depois de T005; T009 depende
  de T005.
- US1 (Fase 3) depende da Fase 2. US2 depende de US1 (convites precisam da conta). US3 depende de
  US2 (cotas só para aceitos); T026 depende de T024 (precisa de `cota_cobranca`). US4 depende de
  US3.
- Testes sempre antes da implementação da história; frontend de cada história depois da sua API.
- T033 e T034 podem ser feitas em paralelo depois de US2.

## Parallel Example

Fase 2: T003 e T005 podem começar juntos; depois T008 e T010 em paralelo.
US3: T021, T022 e T023 (testes) em paralelo; depois T024 → T025, e T026 em paralelo com T025.

## Implementation Strategy

1. MVP: Fases 1 a 3 (US1), mergeável porque nenhuma rota existente muda.
2. Fatia 2: US2 (convites e isolamento), com os testes de 404.
3. Fatia 3: US3 (cobrança e lançamentos), a única que toca código existente (T025 e T026);
   rodar a regressão das suítes de ciclo e lançamentos antes de seguir.
4. Fatia 4: US4 e polish.
