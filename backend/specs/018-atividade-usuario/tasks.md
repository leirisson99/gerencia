# Tasks: Atividade do Usuário no Painel do Administrador

**Input**: documentos em `specs/018-atividade-usuario/`: [plan.md](plan.md), [spec.md](spec.md),
[research.md](research.md), [data-model.md](data-model.md),
[contracts/admin-atividade.md](contracts/admin-atividade.md), [quickstart.md](quickstart.md)

**Tests**: obrigatórios (constituição 6.0.0, princípio III). Cada teste é escrito antes da
implementação e precisa falhar primeiro.

**Caminhos**: backend relativo a `backend/`; frontend em `../frontend/`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode rodar em paralelo (arquivos diferentes, sem dependência pendente)
- **[Story]**: US1–US4 da spec

---

## Phase 1: Setup

- [X] T001 Atualizar `CLAUDE.md` (pendência da emenda 6.0.0):
  - no glossário, a linha "Evento de uso: ação bem-sucedida de uma conta, guardada só com
    usuário, tipo e data e hora; o administrador vê no detalhe da conta, sem conteúdo";
  - no modelo de dados, a linha `evento_uso` (usuario_id, tipo, ocorrido_em);
  - na linha do Administrador do glossário, "vê o uso de cada conta, sem valores nem conteúdo";
  - no item "O projeto", remover "(sem valores e sem nada por usuário)" e trocar por "e o uso
    de cada conta sem valores nem conteúdo".

---

## Phase 2: Foundational (bloqueia todas as histórias)

**Objetivo**: regras puras, tabela, modelo e helper de gravação.

- [X] T002 [P] Escrever `tests/domain/test_atividade.py` cobrindo:
  - `precisa_registrar_visita(ultima: datetime | None, agora: datetime) -> bool`: `True` se
    `ultima is None` ou se `agora - ultima >= 30 min`; `False` com 29 min 59 s;
  - `limite_retencao(agora: datetime) -> datetime`: mesmo dia e hora, 12 meses antes, e
    `2028-02-29T10:00Z` → `2027-02-28T10:00Z`;
  - `tipo_edicao_lembrete(concluido_antes: bool, concluido_depois: bool) -> str`:
    `lembrete_concluido` só quando passa de `False` para `True`, senão `lembrete_editado`;
  - `fatiar_pagina(ids_e_itens: list[T], limite: int) -> tuple[list[T], bool]`: recebe até
    `limite + 1` itens e devolve os `limite` primeiros e se há mais.
- [X] T003 Implementar `app/domain/atividade.py` com as quatro funções do T002 e as constantes
  `JANELA_VISITA = timedelta(minutes=30)`, `MESES_RETENCAO = 12` e `EVENTOS_POR_PAGINA = 50`,
  sem importar banco (depende de T002).
- [X] T004 [P] Criar `app/models/evento_uso.py` com:
  - `TIPOS_EVENTO`: uma tupla com os 27 tipos de [data-model.md](data-model.md), na ordem da
    tabela, e um `Literal` `TipoEvento` com os mesmos valores;
  - a classe `EventoUso` (`__tablename__ = "evento_uso"`) com os campos:
    - `id` bigint `Identity()` PK;
    - `usuario_id` bigint `ForeignKey("usuario.id", ondelete="CASCADE")`;
    - `tipo` `String(30)` com `CheckConstraint("tipo IN (...)", name="tipo")`, montado a partir
      de `TIPOS_EVENTO`;
    - `ocorrido_em` `DateTime(timezone=True)` com `server_default=func.now()`;
  - os índices `ix_evento_uso_usuario_id_id` em `(usuario_id, id.desc())` e
  `ix_evento_uso_ocorrido_em` em `(ocorrido_em)`.
  Exportar o modelo em `app/models/__init__.py`.
- [X] T005 [P] Em `app/models/acao_admin.py`, adicionar `ACAO_VER_ATIVIDADE = "ver_atividade"`
  e incluí-la no `CheckConstraint` de `acao`.
- [X] T006 Criar `alembic/versions/0017_evento_uso.py` (`down_revision` = a última revisão em
  `alembic/versions/`; se a 016 tiver criado uma `0017`, usar o próximo número). A migração cria
  `evento_uso` com o `CHECK` e os índices do T004 e recria o `CHECK acao` de `acao_admin` com
  as 4 ações. O downgrade apaga as linhas `ver_atividade` e volta o `CHECK` às 3 ações
  originais. Rodar `uv run alembic upgrade head` (depende de T004 e T005).
- [X] T007 Criar `app/services/evento_uso.py`:
  - `registrar(db, usuario_id: int, tipo: TipoEvento) -> None`: só faz
    `db.add(EventoUso(...))`, sem commit;
  - `limpar_antigos(db, agora) -> int`: apaga os eventos com
    `ocorrido_em < limite_retencao(agora)`, faz commit e devolve quantos removeu (depende de
    T003 e T004).

**Checkpoint**: `uv run pytest tests/domain/test_atividade.py` verde e migração aplicada.

---

## Phase 3: User Story 2 — gravação dos eventos (Priority: P1)

A gravação vem antes do detalhe porque o US1 e o US2 dependem dela para ter o que mostrar. O
detalhe (US1) funciona sem ela, mas os testes de linha do tempo precisam de eventos gravados.

**Objetivo**: cada ação bem-sucedida grava exatamente um evento; ação que falha não grava
nada.

**Independent Test**: como Ana, criar, editar e excluir um lançamento e conferir 3 linhas em
`evento_uso` com os tipos certos. Um lançamento recusado não pode gravar linha nenhuma.

- [X] T008 [P] [US2] Escrever `tests/api/test_eventos_uso.py`, lendo `evento_uso` direto pela
  sessão de teste, com estes casos:
  - um teste parametrizado por tipo: cada ação da tabela de [data-model.md](data-model.md),
    feita pela rota, grava 1 linha com o `tipo` esperado e o `usuario_id` da Ana;
  - importação confirmada com várias linhas grava 1 `extrato_importado` e nenhum
    `lancamento_criado`;
  - lançar o salário que abre ciclo com recorrência ativa grava só 1 `lancamento_criado`;
  - criar dívida com 3 parcelas grava só 1 `divida_criada`;
  - lançamento antes do primeiro salário (erro) grava 0 linhas;
  - login com senha errada e login de conta desativada gravam 0 linhas;
  - login do administrador grava 0 linhas;
  - editar lembrete com `concluido: true` grava `lembrete_concluido`, e só com texto grava
    `lembrete_editado`;
  - nenhuma coluna de `evento_uso` além de `id`, `usuario_id`, `tipo` e `ocorrido_em` (checar
    `EventoUso.__table__.columns`).
- [X] T009 [US2] Chamar `registrar(db, usuario.id, "conta_criada")` em `auth.cadastrar`;
  `"login"` em `auth.entrar` depois da senha conferida e só se `usuario.papel == PAPEL_USUARIO`;
  e `"senha_trocada"` em `auth.trocar_senha`, sempre antes do `commit` existente em
  `app/services/auth.py` (depende de T007 e T008).
- [X] T010 [P] [US2] Chamar `registrar` antes do commit, na mesma transação, em:
  - `perfil_atualizado` em `app/services/perfil.py`;
  - `lancamento_criado`, `lancamento_editado` e `lancamento_excluido` em
    `app/services/lancamento.py`;
  - `extrato_importado` em `importacao.confirmar`, uma vez por chamada, em
    `app/services/importacao.py`.
- [X] T011 [P] [US2] Chamar `registrar` antes do commit em:
  - `categoria_criada` e `categoria_editada` em `app/services/categoria.py` (dentro do
    `_gravar`, ou antes dele, sem afetar `criar_categorias_iniciais`, que não gera evento);
  - `recorrencia_criada` e `recorrencia_editada` em `app/services/recorrencia.py`;
  - `divida_criada` em `app/services/divida.py`.
- [X] T012 [P] [US2] Chamar `registrar` antes do commit em:
  - `cartela_criada`, `deposito_feito` e `deposito_desfeito` em `app/services/cartela.py`;
  - `servico_criado`, `servico_editado`, `servico_excluido`, `servico_recebido` e
    `recebimento_desfeito` em `app/services/servico.py`.
- [X] T013 [P] [US2] Chamar `registrar` antes do commit em:
  - `lembrete_criado` e `lembrete_excluido` em `app/services/lembrete.py`;
  - em `editar_livre`, o tipo de `tipo_edicao_lembrete(lembrete.concluido, novo_concluido)`,
    calculado antes de aplicar a mudança;
  - `push_ativado` em `push.inscrever` e `push_removido` em `push.remover_inscricao`, só quando
    algo foi gravado ou removido, em `app/services/push.py`.

**Checkpoint**: `uv run pytest tests/api/test_eventos_uso.py` verde e a suíte inteira continua
verde.

---

## Phase 4: User Story 1 — detalhe da conta (Priority: P1) 🎯 MVP

**Objetivo**: `GET /api/v1/admin/usuarios/{id}` com conta, acesso, sessões e contagens.

**Independent Test**: Ana com 5 lançamentos manuais, 3 importados, 1 cartela com 2 depósitos
e nenhum serviço; o detalhe traz cada número certo e nenhum valor ou texto dela.

- [X] T014 [P] [US1] Escrever `tests/api/test_admin_atividade.py` (parte do detalhe) com estes
  casos:
  - cada contagem do contrato, com zero no que não é usado;
  - `lancamentos_gerados` conta recorrência, parcela, depósito de cartela e serviço, e não
    conta como manual;
  - `importacoes` igual ao número de eventos `extrato_importado`;
  - `sessoes_abertas` = 2 com dois logins, e uma sessão vencida por inatividade não conta;
  - `ultimo_acesso_em` `null` para conta sem acesso;
  - conta desativada: abre, com 0 sessões;
  - 404 para id inexistente e para o id do administrador;
  - 403 `acesso_negado` para usuário comum, inclusive na própria conta;
  - 401 sem sessão;
  - teste de privacidade: plantar descrição `"SEGREDO-DESC"`, categoria `"SEGREDO-CAT"`,
    cliente `"SEGREDO-CLI"`, cartela `"SEGREDO-CART"`, lembrete `"SEGREDO-LEMB"`, telefone,
    cargo e valor `123457`. Depois, verificar que nenhuma dessas strings aparece no JSON do
    detalhe.
- [X] T015 [US1] Em `app/schemas/admin.py`, criar:
  - `ContagensContaOut`, com 11 campos `int` na ordem do contrato;
  - `AcaoAdminOut`, com `acao: Literal["reset_senha", "desativar_conta", "reativar_conta",
    "ver_atividade"]`, `ocorrida_em: datetime` e `admin_nome: str`;
  - `DetalheContaOut`, com `conta: UsuarioAdminOut`, `ultimo_acesso_em: datetime | None`,
    `sessoes_abertas: int`, `contagens: ContagensContaOut` e `acoes_admin: list[AcaoAdminOut]`
    (depende de T014).
- [X] T016 [US1] Em `app/services/admin.py`, criar:
  - `_registrar_visita(db, admin, usuario, agora)`: busca a última `ver_atividade` desse admin
    nessa conta e grava uma nova se `precisa_registrar_visita` mandar;
  - `obter_detalhe(db, admin, usuario_id, agora, dias_sessao) -> DetalheContaOut`, que:
    - usa `_conta_alvo` e chama `_registrar_visita` com commit;
    - conta numa consulta só, com subconsultas escalares no padrão de `_contas`:
      - `lancamentos_importados`: `id_externo` preenchido;
      - `lancamentos_gerados`: sem `id_externo` e com `recorrencia_id` ou `divida_id`, ou com
        `id` em `casa.lancamento_id` ou `servico.lancamento_id`;
      - `lancamentos_manuais`: o resto;
      - `importacoes`: eventos `extrato_importado`;
      - recorrências, dívidas, cartelas, `depositos` (casas com `depositado_em` preenchido),
        serviços, lembretes e `aparelhos_push` (`inscricao_push`);
    - calcula `sessoes_abertas` com `Sessao.ultimo_uso_em >= agora - timedelta(days=dias_sessao)`,
      o mesmo critério de `domain/login.sessao_expirada`;
    - busca as últimas 50 `acao_admin` da conta, juntando o nome do admin, da mais recente para
      a mais antiga.
- [X] T017 [US1] Em `app/api/routes/admin.py`, criar `GET /usuarios/{usuario_id}` com
  `responses=ALVO`. A rota chama `obter_detalhe(db, admin, usuario_id, relogio.agora_utc(),
  settings.sessao_dias_inatividade)` e devolve `DetalheContaOut`. Ela precisa ser declarada
  sem conflitar com as rotas `POST /usuarios/{id}/...` que já existem.
- [X] T018 [P] [US1] Frontend: em `../frontend/lib/api/admin.ts`, criar os tipos
  `DetalheConta`, `ContagensConta` e `AcaoAdmin`, a função `obterDetalheConta(id)` e o mapa
  `ROTULOS_ACAO_ADMIN`.
- [X] T019 [US1] Frontend: criar `../frontend/app/(admin)/admin/contas/[id]/page.tsx` e
  `../frontend/features/admin/detalhe-conta.tsx`. A página mostra o cabeçalho (nome, e-mail,
  criado em, selo de situação, ações existentes de `acoes-conta.tsx`), os cartões "Último
  acesso" ("nunca" quando nulo) e "Sessões abertas" e a grade de contagens com rótulos em
  português, em largura total, no tema preto, branco, cinza e vermelho. O 404 mostra "Conta não
  encontrada" e um link para voltar (depende de T018).
- [X] T020 [US1] Frontend: em `../frontend/features/admin/lista-contas.tsx`, tornar o nome ou a
  linha de cada conta um link para `/admin/contas/{id}`, sem quebrar os botões de ação da linha
  (que não devem navegar).

**Checkpoint**: o detalhe abre pela lista e os testes do T014 estão verdes.

---

## Phase 5: User Story 2 — linha do tempo (Priority: P1)

**Objetivo**: `GET /api/v1/admin/usuarios/{id}/eventos?antes=` paginado e exibido no detalhe.

**Independent Test**: com 120 eventos da Ana e alguns do Bruno, 3 páginas (50, 50, 20) trazem
só os da Ana, sem repetir, e a última tem `proximo: null`.

- [X] T021 [P] [US2] Em `tests/api/test_admin_atividade.py`, testar a linha do tempo:
  - a ordem é do mais recente para o mais antigo;
  - as páginas de 50 itens seguem `proximo` → `antes` sem repetir nem pular, mesmo com um evento
    novo gravado entre uma página e outra;
  - só aparecem eventos da conta pedida;
  - os itens têm só `tipo` e `ocorrido_em`;
  - `antes=0` e `antes=abc` respondem 422;
  - 403, 404 e 401 como no detalhe.
- [X] T022 [US2] Em `app/schemas/admin.py`, criar `EventoUsoOut` (`tipo: TipoEvento`,
  `ocorrido_em: datetime`) e `PaginaEventosOut` (`itens: list[EventoUsoOut]`,
  `proximo: int | None`).
- [X] T023 [US2] Em `app/services/admin.py`, criar `listar_eventos(db, admin, usuario_id,
  antes: int | None, agora) -> PaginaEventosOut`. A função usa `_conta_alvo` e
  `_registrar_visita`, consulta `evento_uso` com `usuario_id`, `id < antes` quando houver,
  `order by id desc` e `limit EVENTOS_POR_PAGINA + 1`. Depois aplica `fatiar_pagina`: se houver
  mais, `proximo` é o `id` do último item devolvido.
- [X] T024 [US2] Em `app/api/routes/admin.py`, criar `GET /usuarios/{usuario_id}/eventos`, com
  `antes: Annotated[int | None, Query(gt=0)] = None` e `responses=ALVO`.
- [X] T025 [P] [US2] Frontend: em `../frontend/lib/api/admin.ts`, criar o tipo `EventoUso`, a
  função `listarEventos(id, antes?)` e o mapa `ROTULOS_EVENTO` com os 27 rótulos da tabela de
  [data-model.md](data-model.md).
- [X] T026 [US2] Frontend: criar `../frontend/features/admin/linha-tempo.tsx` e incluí-lo em
  `detalhe-conta.tsx`. A lista mostra rótulo e data e hora em `America/Sao_Paulo`, agrupada por
  dia, com o botão "Carregar mais" enquanto `proximo` não for nulo. Lista vazia mostra "Sem
  atividade registrada desde 02/10/2026", com a data da entrada da feature numa constante
  (depende de T025).

**Checkpoint**: a linha do tempo pagina no navegador e os testes do T021 estão verdes.

---

## Phase 6: User Story 3 — ações do administrador sobre a conta (Priority: P2)

**Objetivo**: histórico de ações no detalhe e auditoria `ver_atividade`.

**Independent Test**: resetar a senha, desativar, reativar e abrir o detalhe; as 4 ações
aparecem, da mais recente para a mais antiga.

- [X] T027 [P] [US3] Em `tests/api/test_admin_atividade.py`, testar:
  - abrir o detalhe grava 1 `ver_atividade`;
  - abrir de novo e paginar eventos dentro de 30 min não gravam outra (relógio falso);
  - depois de 30 min, grava de novo;
  - chamar só `/eventos` também grava;
  - `acoes_admin` lista reset, desativação, reativação e `ver_atividade` com `admin_nome`, e não
    traz ações sobre o Bruno.
- [X] T028 [US3] Ajustar o que os testes do T027 pedirem em `app/services/admin.py`
  (`_registrar_visita`, ordem e limite de `acoes_admin`).
- [X] T029 [P] [US3] Frontend: em `detalhe-conta.tsx`, criar a seção "Ações do administrador",
  em tabela compacta com ação (rótulo de `ROTULOS_ACAO_ADMIN`), quem fez e quando. Lista vazia
  mostra "Nenhuma ação registrada".

---

## Phase 7: User Story 4 — aviso de transparência (Priority: P1)

**Objetivo**: avisar o usuário no cadastro e no perfil.

**Independent Test**: abrir a tela de cadastro e o perfil e ver o aviso nos dois.

- [X] T030 [P] [US4] Criar `../frontend/components/aviso-uso-admin.tsx` com o texto fixo "O
  administrador vê quando você entra e quais recursos usa, mas nunca valores, descrições ou
  nomes do que você lança.", em estilo discreto (texto pequeno, cinza, ícone de informação).
- [X] T031 [US4] Incluir `<AvisoUsoAdmin />` em `../frontend/features/auth/form-cadastro.tsx`,
  logo acima do botão de criar conta, e em `../frontend/features/perfil/form-perfil.tsx`
  (depende de T030).

---

## Phase 8: Polish & Cross-Cutting

- [X] T032 [P] Em `tests/domain/test_atividade.py` ou `tests/api/test_eventos_uso.py`, testar
  `limpar_antigos`: um evento com 12 meses e 1 dia é removido, um com 11 meses fica, e o
  retorno é a contagem.
- [X] T033 Em `app/cli.py`, criar o subcomando `limpar-eventos`, que abre `SessionLocal`, chama
  `limpar_antigos(db, Relogio().agora_utc())` e imprime só `removidos=<n>`. Em `crontab`,
  acrescentar a linha comentada `0 6 * * * python -m app.cli limpar-eventos` (3h em São Paulo).
- [X] T034 [P] Atualizar `specs/018-atividade-usuario/spec.md` (Status) e esta lista ao final.
  Atualizar o quickstart se algo mudar.
- [X] T035 Rodar `uv run pytest`, `uv run ruff check .` e `uv run ruff format .` no backend, e
  `npm run lint` e `npm run build` no frontend. Corrigir o que falhar.
- [ ] T036 Validar os cenários de [quickstart.md](quickstart.md) de ponta a ponta com a API e o
  frontend no ar.

---

## Dependencies & Execution Order

- **Setup (T001)**: independente.
- **Foundational (T002–T007)**: bloqueia tudo. T002 → T003; T004 e T005 → T006; T003 e T004 →
  T007.
- **US2, gravação (T008–T013)**: depende da Foundational. T009–T013 tocam arquivos
  diferentes e rodam em paralelo depois do T008.
- **US1 (T014–T020)**: depende da Foundational, e o `importacoes` usa os eventos do T010. O
  backend (T014–T017) antes de T019 e T020; T018 em paralelo.
- **US2, linha do tempo (T021–T026)**: depende de T016 (`_registrar_visita`) e da gravação.
- **US3 (T027–T029)**: depende de US1 e da linha do tempo.
- **US4 (T030–T031)**: independente de tudo; pode ser feita a qualquer momento, mas precisa ir
  ao ar junto com o detalhe.
- **Polish (T032–T036)**: no fim; T032 → T033.

## Parallel Example

```text
# Depois da Foundational:
T008 (testes de gravação) | T014 (testes do detalhe) | T030 (aviso)
# Depois do T008:
T010 | T011 | T012 | T013
# Frontend enquanto o backend do US1 anda:
T018 | T025
```

## Implementation Strategy

1. **MVP**: Foundational + gravação (US2) + detalhe (US1) + aviso (US4). O admin já vê se a
   pessoa entra e o que usa.
2. **Incremento 2**: linha do tempo (US2), para ver onde a pessoa travou.
3. **Incremento 3**: histórico de ações do admin (US3) e retenção (Polish).
4. Um commit por fase, em Conventional Commits:
   - `feat: eventos de uso`;
   - `feat: detalhe da conta no painel admin`;
   - `feat: linha do tempo de uso`;
   - `feat: aviso de uso ao usuário`;
   - `chore: limpeza de eventos no cron`.
