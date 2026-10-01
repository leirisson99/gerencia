# Tasks: Lembretes por Push

**Input**: [plan.md](plan.md), [spec.md](spec.md), [data-model.md](data-model.md),
[contracts/api.md](contracts/api.md), [research.md](research.md), [quickstart.md](quickstart.md)

**Tests**: obrigatórios (Constituição, Princípio III). O domínio tem teste escrito antes. Os
endpoints têm teste de API contra PostgreSQL. O envio é testado com um enviador falso, sem rede.
O isolamento financeiro fica no arquivo de teste da própria feature, como nas features
anteriores.

**Caminhos**: o backend é relativo a `backend/` e o frontend, a `frontend/`. Antes de escrever
código Next, leia o guia em `frontend/node_modules/next/dist/docs/` (AGENTS.md do frontend).

## Phase 1: Setup

- [X] T001 Confirmar a base verde em `backend/`: `uv run pytest -q` e `uv run ruff check .`. Em `frontend/`: `npm run lint`.
- [X] T002 Adicionar `pywebpush>=2.5` às dependências em backend/pyproject.toml (`uv add pywebpush`) e conferir que `uv run python -c "import pywebpush"` funciona.
- [X] T003 Em backend/app/config.py, adicionar as configurações `vapid_chave_publica: str | None = None`, `vapid_chave_privada: str | None = None` e `vapid_contato: str | None = None`. Em backend/.env.example, documentar `VAPID_CHAVE_PUBLICA=`, `VAPID_CHAVE_PRIVADA=` e `VAPID_CONTATO=mailto:...`, com valores vazios.

## Phase 2: Foundational (bloqueia todas as histórias)

- [X] T004 [P] Testes de domínio em backend/tests/domain/test_lembrete.py, escritos antes e começando no vermelho:
  - `situacao(data, hoje)`: `atrasado` para ontem e para 30 dias atrás; `a_vencer` para hoje, hoje + 1 e hoje + 3; `None` para hoje + 4.
  - `JANELA_DIAS == 3` e `limite(hoje) == hoje + 3`, inclusive na virada de mês e de ano (30/12 → 02/01).
  - `contar(itens)`: soma atrasados e a vencer por origem (`conta`, `valor`, `livre`).
  - `texto_resumo(contagem, hoje)`:
    - `None` quando o total é zero;
    - título `Gerencia`;
    - corpo com as partes, a ordem, o separador ` · `, o sufixo, o singular e o plural (conta/contas, atrasada/atrasadas, valor/valores, atrasado/atrasados, lembrete/lembretes) e o dia da semana sem "-feira", exatamente como na seção "Resumo da notificação" de data-model.md, incluindo os dois exemplos;
    - o corpo nunca contém `R$`, dígito seguido de vírgula, nem textos passados nos itens.
- [X] T005 Implementar em backend/app/domain/lembrete.py as funções puras `JANELA_DIAS`, `limite`, `Situacao` (Literal), `situacao`, `Origem` (Literal `"conta" | "valor" | "livre"`), `Contagem` (dataclass com `atrasados` e `a_vencer` por origem), `contar`, `Mensagem` (dataclass com `titulo` e `corpo`) e `texto_resumo`, até T004 passar. Sem banco, sem relógio e sem textos dos itens.
- [X] T006 Criar a migração backend/alembic/versions/0015_lembretes_push.py (`down_revision` = 0014):
  - tabela `lembrete`:
    - `id BIGINT IDENTITY` PK;
    - `usuario_id BIGINT NOT NULL` FK `usuario.id` `ON DELETE CASCADE`;
    - `texto VARCHAR(200) NOT NULL`, `data DATE NOT NULL`;
    - `concluido_em TIMESTAMPTZ NULL`, `criado_em TIMESTAMPTZ NOT NULL DEFAULT now()`;
    - índice `(usuario_id, data)`.
  - tabela `inscricao_push`:
    - `id BIGINT IDENTITY` PK;
    - `usuario_id BIGINT NOT NULL` FK `usuario.id` `ON DELETE CASCADE`, com índice;
    - `endpoint TEXT NOT NULL UNIQUE`;
    - `p256dh VARCHAR(200) NOT NULL`, `auth VARCHAR(100) NOT NULL`;
    - `criado_em TIMESTAMPTZ NOT NULL DEFAULT now()`.
  - tabela `envio_lembrete`:
    - `usuario_id BIGINT` FK `usuario.id` `ON DELETE CASCADE`;
    - `dia DATE`;
    - PK `(usuario_id, dia)`;
    - `enviado_em TIMESTAMPTZ NOT NULL DEFAULT now()`.
  - `downgrade` remove as três tabelas.
  - Testar com `uv run alembic upgrade head`, depois `downgrade -1` e `upgrade head`.
- [X] T007 Criar os modelos `Lembrete`, `InscricaoPush` e `EnvioLembrete` em backend/app/models/lembrete.py, espelhando a migração, e registrá-los em backend/app/models/__init__.py.

## Phase 3: User Story 1 — Ver o que vence nos próximos dias (P1) 🎯 MVP

**Goal**: `GET /api/v1/lembretes` e a página `/lembretes` com contas e valores atrasados e a
vencer.

**Independent Test**: aluguel previsto para daqui a 2 dias, internet prevista para ontem e
serviço a receber daqui a 5 dias. Ao abrir os lembretes, a internet aparece em "atrasados", o
aluguel em "a vencer" e o serviço não aparece.

- [X] T008 [US1] Testes de API em backend/tests/api/test_lembretes.py, escritos antes e começando no vermelho (relógio fixo em 10/10/2026; fixtures de usuário com salário):
  - Saídas previstas com data em 09/10, 10/10, 13/10 e 14/10: as duas primeiras ficam em `atrasados` e `a_vencer`, 13/10 em `a_vencer`, e 14/10 fica de fora. Conferir `hoje`, `limite`, `origem: "conta"` e `lancamento` completo.
  - Entrada prevista em 11/10 → `origem: "valor"`.
  - Previstos de ciclos anteriores aparecem como atrasados.
  - Não aparecem: parcela com `conta_no_saldo = False`, lançamento realizado (aparece de novo ao voltar a previsto) e depósito de cartela.
  - Ordem por data e id.
  - Prestador sem salário também funciona.
  - Isolamento: lançamentos de outro usuário nunca aparecem.
- [X] T009 [US1] Criar os schemas em backend/app/schemas/lembrete.py: `ItemLembrete` (`origem`, `situacao`, `data`, `lancamento: LancamentoOut | None`, `lembrete: LembreteLivreOut | None`) e `LembretesOut` (`hoje`, `limite`, `atrasados`, `a_vencer`), conforme contracts/api.md.
- [X] T010 [US1] Em backend/app/services/lembrete.py, criar `pendencias_de_lancamento(db, usuario_id, hoje)`. Uma consulta: `usuario_id`, `status = 'previsto'`, `data <= limite(hoje)`, (`tipo = 'entrada'` OR `conta_no_saldo`), ordenada por `data` e `id`. Criar também `listar_lembretes(db, usuario_id, hoje) -> LembretesOut`, que classifica com `domain.lembrete.situacao`.
- [X] T011 [US1] Criar a rota `GET /api/v1/lembretes` (com `AutenticadoDep` e `RelogioDep`) em backend/app/api/routes/lembretes.py e incluir o router em backend/app/main.py.
- [X] T012 [P] [US1] No frontend, criar os tipos `OrigemLembrete`, `SituacaoLembrete`, `ItemLembrete`, `LembretesOut` e `LembreteLivre` em frontend/lib/api/types.ts, e `obterLembretes()` em frontend/lib/api/server.ts.
- [X] T013 [US1] Criar a página frontend/app/(app)/lembretes/page.tsx (server component com `PageHeader`, largura total) e a lista frontend/features/lembretes/lista-lembretes.tsx:
  - seções "Atrasados" (em vermelho) e "A vencer até <limite>";
  - cada item mostra data, categoria, descrição e valor com sinal, reaproveitando o estilo de `ListaLancamentos`;
  - item de lançamento abre a edição em `DialogLancamento`;
  - estado vazio "Nada vencendo nos próximos 3 dias."
- [X] T014 [US1] Adicionar o item "Lembretes" (`BellIcon`, href `/lembretes`) ao grupo "Visão" em frontend/components/layout/app-sidebar.tsx.

**Checkpoint**: a página mostra as pendências corretas, sem push.

## Phase 4: User Story 2 — Receber o resumo diário no celular (P1)

**Goal**: comando `enviar-lembretes` com no máximo um resumo por dia, só com contagens, e remoção
de aparelhos recusados.

**Independent Test**: com inscrições criadas direto no banco e um enviador falso, rodar o envio,
receber uma mensagem com as contagens, rodar de novo e não receber outra.

- [X] T015 [US2] Testes de serviço em backend/tests/services/test_envio_lembrete.py, escritos antes e começando no vermelho. O `EnviadorFalso` registra as chamadas e devolve `ok`, `expirado` (404/410) ou `falha` por endpoint. Casos:
  - Usuário com 2 contas a vencer e 1 valor atrasado: uma mensagem por aparelho, com `titulo`, `corpo` igual a `texto_resumo` e `url` `/lembretes`. O corpo não contém valores nem descrições.
  - Rodar de novo no mesmo dia não chama o enviador (`ja_enviados`).
  - Usuário sem pendências não recebe (`sem_pendencias`). Usuário sem aparelho é ignorado.
  - Conta desativada (`ativo = False`) e administrador são ignorados.
  - Dois aparelhos, um `expirado`: a inscrição expirada é apagada (`removidos=1`) e o outro recebe.
  - Todos os aparelhos com `falha`: a reserva de `envio_lembrete` é apagada (`falhas=1`) e uma segunda execução no mesmo dia tenta de novo.
  - Reserva já existente no dia (execução concorrente): não envia.
- [X] T016 [US2] Em backend/app/services/envio_lembrete.py, criar:
  - `ResultadoEnvio` (Literal `"ok" | "expirado" | "falha"`);
  - o protocolo `Enviador` (`enviar(inscricao, payload: dict) -> ResultadoEnvio`);
  - `Relatorio` (dataclass só com contagens);
  - `enviar_lembretes_do_dia(db, hoje, enviador) -> Relatorio`.

  A função percorre os usuários `ativo` e com papel `usuario` que têm inscrições. Para cada um:
  - conta as pendências com `pendencias_de_lancamento` (e, depois da US4, os livres);
  - sem mensagem, pula;
  - reserva o dia com `INSERT ... ON CONFLICT DO NOTHING RETURNING` e commit;
  - envia para cada aparelho e apaga os `expirado`;
  - se nenhum `ok`, apaga a reserva;
  - faz commit por usuário.
- [X] T017 [US2] Criar o adaptador `EnviadorWebPush` em backend/app/push.py:
  - usa `pywebpush.webpush` com `subscription_info` `{endpoint, keys: {p256dh, auth}}`, `data=json.dumps(payload)`, `vapid_private_key`, `vapid_claims={"sub": vapid_contato}`, `ttl=43200` e header `Urgency: normal`;
  - `WebPushException` com status 404 ou 410 vira `expirado`; outros erros e exceções de rede viram `falha`;
  - nunca registra endpoint nem payload em log.
- [X] T018 [US2] Adicionar dois subcomandos em backend/app/cli.py:
  - `enviar-lembretes`: sem as chaves VAPID, imprime a mensagem em stderr e devolve 1. Com as chaves, usa `Relogio().hoje_sp()`, `SessionLocal` e `EnviadorWebPush`, e imprime uma linha `usuarios=… enviados=… sem_pendencias=… ja_enviados=… removidos=… falhas=…`.
  - `gerar-chaves-vapid`: gera o par com `py_vapid.Vapid` e imprime `VAPID_CHAVE_PUBLICA=…` (ponto não comprimido em base64url) e `VAPID_CHAVE_PRIVADA=…` (base64url).

  Atualizar o docstring do módulo. (`gerar-chaves-vapid` e os testes dele já estão feitos,
  adiantados em 2026-10-01; falta `enviar-lembretes`.) Testar em backend/tests/services/test_cli.py: `enviar-lembretes` sem chaves devolve 1, e `gerar-chaves-vapid` imprime as duas variáveis.
- [X] T019 [P] [US2] Criar o service worker frontend/public/sw.js:
  - `push`: lê `{titulo, corpo, url}` e chama `showNotification(titulo, {body: corpo, icon: "/icone-192.png", badge: "/icone-192.png", tag: "lembretes", data: {url}})`.
  - `notificationclick`: fecha a notificação e foca uma janela do app, navegando para `url`, ou chama `clients.openWindow(url)`.
- [X] T020 [P] [US2] Em frontend/next.config.ts, adicionar `headers()` para `/sw.js` com `Content-Type: application/javascript; charset=utf-8`, `Cache-Control: no-cache, no-store, must-revalidate` e `Service-Worker-Allowed: /`, preservando os rewrites existentes.

**Checkpoint**: com uma inscrição real (US3), o comando entrega o resumo uma vez por dia.

## Phase 5: User Story 3 — Ativar e desativar as notificações (P1)

**Goal**: rotas de push, seção no Perfil e desinscrição ao sair.

**Independent Test**: ativar no Perfil, ver "ativadas neste aparelho", desativar e não receber
mais o resumo nesse aparelho.

- [X] T021 [US3] Testes de API em backend/tests/api/test_push.py, escritos antes e começando no vermelho:
  - `GET /push/chave` devolve a chave configurada, ou 503 `push_indisponivel` sem chaves (sobrescrever as settings no teste).
  - `PUT /push/inscricao` cria (204). O mesmo endpoint de novo atualiza as chaves sem duplicar. O endpoint de Bia, quando Ana faz `PUT`, passa a ser de Ana.
  - Validações 422: endpoint `http://` ou com mais de 2048 caracteres, `keys` ausentes, campo extra. `expirationTime` é aceito.
  - `PUT` sem chaves VAPID → 503.
  - `DELETE /push/inscricao` remove (204). Endpoint inexistente ou de outro usuário → 404 `nao_encontrado`, sem apagar a inscrição do outro.
  - Sem sessão → 401.
- [X] T022 [US3] Criar os schemas em backend/app/schemas/push.py:
  - `ChavePushOut(chave_publica: str)`;
  - `ChavesInscricao(p256dh: str ≤ 200, auth: str ≤ 100)`;
  - `InscricaoIn(endpoint: str` iniciando com `https://` e com no máximo 2048 caracteres, `keys: ChavesInscricao`, `expirationTime: int | None = None`), com `extra="forbid"`;
  - `InscricaoRemoverIn(endpoint: str)`.
- [X] T023 [US3] Em backend/app/services/push.py, criar:
  - `inscrever(db, usuario_id, dados)`: upsert por `endpoint` com `INSERT ... ON CONFLICT (endpoint) DO UPDATE SET usuario_id, p256dh, auth`;
  - `remover_inscricao(db, usuario_id, endpoint)`: 404 se não houver linha desse usuário com esse endpoint;
  - `chave_publica(settings)`: 503 `push_indisponivel`, "As notificações não estão disponíveis no momento.", quando faltar alguma chave.
- [X] T024 [US3] Criar as rotas `GET /api/v1/push/chave`, `PUT /api/v1/push/inscricao` e `DELETE /api/v1/push/inscricao` (corpo `InscricaoRemoverIn`) em backend/app/api/routes/push.py e incluir o router em backend/app/main.py.
- [X] T025 [P] [US3] Criar no frontend `obterChavePush()`, `inscreverAparelho(sub)` e `removerAparelho(endpoint)` em frontend/lib/api/push.ts.
- [X] T026 [US3] Criar frontend/lib/push.ts (só cliente):
  - `estadoPush()`, que devolve um dos estados `"sem_suporte" | "iphone_sem_instalar" | "bloqueado" | "inativo" | "ativo"`. Detectar `serviceWorker`, `PushManager`, `Notification.permission`, iOS e `display-mode: standalone` ou `navigator.standalone`.
  - `registrarServiceWorker()`, com `register("/sw.js", {scope: "/", updateViaCache: "none"})`.
  - `ativarPush()`: pede a permissão, faz `subscribe({userVisibleOnly: true, applicationServerKey})` a partir de `obterChavePush()` e chama `inscreverAparelho`.
  - `desativarPush()`: chama `removerAparelho`, ignora 404, e faz `unsubscribe`.
  - `sincronizarPush()`: se já existe inscrição local, chama `PUT` de novo.
- [X] T027 [US3] Criar frontend/features/perfil/secao-notificacoes.tsx e adicioná-la a frontend/app/(app)/(coluna)/perfil/page.tsx, entre `FormPerfil` e `SecaoSenha`, com `Separator`.
  - Mostra o estado, o botão "Ativar notificações" ou "Desativar neste aparelho", e as instruções para os estados bloqueado, iPhone sem instalar ("Adicione o app à tela inicial…") e sem suporte.
  - Esconde a ativação se `obterChavePush` der 503.
  - Ao montar, chama `sincronizarPush()`.
  - Mostra toasts de sucesso e de erro.
- [X] T028 [US3] Em frontend/features/auth/use-sair.ts, chamar `desativarPush()` antes de `sair()`, com try/catch, sem bloquear o logout.

**Checkpoint**: o fluxo completo funciona em `http://localhost`: ativar, rodar `enviar-lembretes`, receber a notificação e tocar para abrir `/lembretes`.

## Phase 6: User Story 4 — Criar lembretes livres (P2)

**Goal**: lembretes livres na página, na janela e no resumo.

**Independent Test**: criar "renovar seguro" para depois de amanhã, vê-lo em "a vencer" e no
resumo, concluir e vê-lo sair.

- [X] T029 [US4] Testes de API em backend/tests/api/test_lembretes.py, escritos antes e começando no vermelho:
  - Criar → 201 com `concluido: false`.
  - Validações 422: `texto` vazio, só com espaços ou com mais de 200 caracteres; `data` ausente; campo extra.
  - Listar `/lembretes/livres` por data e id, incluindo concluídos e futuros.
  - `PATCH` de texto e data. `concluido: true` grava `concluido_em`; `false` limpa. `null` em qualquer campo → 422.
  - `DELETE` → 204.
  - Lembrete livre não concluído aparece em `GET /lembretes` com `origem: "livre"` (atrasado ou a vencer); fora da janela ou concluído não aparece.
  - Outro usuário → 404 em `PATCH` e `DELETE`.
- [X] T030 [US4] Adicionar a backend/app/schemas/lembrete.py: `LembreteLivreIn` (`texto` "obrigatório, até 200 caracteres", aparado com `limpar_texto`, e `data: date`, com `extra="forbid"`), `LembreteLivrePatch` (`texto?`, `data?`, `concluido?: bool`, sem `null`) e `LembreteLivreOut` (`id`, `texto`, `data`, `concluido`, `concluido_em`, `criado_em`).
- [X] T031 [US4] Em backend/app/services/lembrete.py, criar `criar_livre`, `listar_livres`, `editar_livre` (que define `concluido_em` com `relogio.agora_utc()`) e `excluir_livre`, com 404 `nao_encontrado` "Lembrete não encontrado." para lembrete de outro usuário. Incluir os livres pendentes da janela em `listar_lembretes`.
- [X] T032 [US4] Criar as rotas `GET` e `POST /api/v1/lembretes/livres`, `PATCH` e `DELETE /api/v1/lembretes/livres/{id}` em backend/app/api/routes/lembretes.py.
- [X] T033 [US4] Incluir os livres pendentes da janela na contagem de `enviar_lembretes_do_dia` (origem `livre`) em backend/app/services/envio_lembrete.py, com o caso correspondente em backend/tests/services/test_envio_lembrete.py: só um lembrete livre a vencer gera "1 lembrete até …", e o texto do lembrete não aparece.
- [X] T034 [P] [US4] No frontend, criar os tipos `LembreteLivreIn` e `LembreteLivrePatch` em frontend/lib/api/types.ts, as funções `criarLembreteLivre`, `editarLembreteLivre` e `excluirLembreteLivre` em frontend/lib/api/lembretes.ts, e `listarLembretesLivres()` em frontend/lib/api/server.ts.
- [X] T035 [US4] Criar frontend/features/lembretes/dialog-lembrete-livre.tsx, com texto (máximo 200) e data, no padrão de `dialog-recorrencia.tsx`, incluindo o botão de excluir com `AlertDialog`. Na lista, adicionar:
  - o botão "Novo lembrete";
  - na janela, os livres com o botão "Concluir";
  - a seção "Próximos lembretes" (futuros fora da janela);
  - a seção "Concluídos" recolhida em `<details>`, com "Desfazer".

## Phase 7: Polish & Cross-Cutting

- [X] T036 [P] Conferir que nenhum log do envio, das rotas de push ou do CLI imprime endpoint, chaves, valores ou textos, com grep em backend/app/services/envio_lembrete.py, backend/app/push.py e backend/app/cli.py.
- [X] T037 Rodar `uv run pytest`, `uv run ruff check .` e `uv run ruff format --check .` em `backend/`, e `npm run lint` e `npm run build` em `frontend/`.
- [x] T038 Validar ponta a ponta os cenários 1 a 9 de quickstart.md em `http://localhost` (backend atual, frontend em dev).
  - Feito em 2026-10-01: cenários 1, 2, 5, 8 e 9 pela API e pela página, e o comando de envio
    com as chaves reais. Pendente: 3, 4, 6 e 7, que exigem clicar em "Ativar" e aceitar a
    permissão no navegador.
- [X] T039 Marcar o status da spec como implementada em specs/015-lembretes-push/spec.md e conferir o CLAUDE.md (glossário e modelo de dados já atualizados).
- [X] T040 Criar backend/Dockerfile.cron para o serviço `lembretes` do Easypanel: mesma base e build do backend/Dockerfile (código e `.venv`), com o binário do supercronic instalado e um crontab `CRON_TZ=America/Sao_Paulo` / `0 8 * * * python -m app.cli enviar-lembretes`; `CMD ["supercronic", "/app/crontab"]`, sem rodar migrações nem a API. Documentar em quickstart.md, na seção de produção, como criar o serviço no Easypanel (mesmo repositório, Dockerfile `backend/Dockerfile.cron`, mesmas variáveis `DATABASE_URL` e `VAPID_*`) e trocar o exemplo de cron do servidor por ele

## Dependencies

- **Setup (T001–T003)** → **Foundational (T004–T007)** → histórias.
- **US1 (T008–T014)**: depende só da fundação. É o MVP.
- **US2 (T015–T020)**: depende de US1, porque usa `pendencias_de_lancamento` (T010). Os testes criam inscrições direto no banco, então US2 não depende das rotas de US3.
- **US3 (T021–T028)**: depende só da fundação para o backend. O teste de ponta a ponta precisa de US2 (sw.js e comando).
- **US4 (T029–T035)**: depende de US1 (T010 e T013) e, para T033, de US2 (T016).
- **Polish**: depois de todas.

Dentro de cada história, o teste vem antes, no vermelho. Depois: schemas, services, rotas e
frontend.

## Parallel Opportunities

- T004 (testes de domínio) e T006 (migração) podem andar juntos; T005 depende de T004 e T007, de T006.
- US1: T012 (tipos do frontend) em paralelo com T009–T011 (backend).
- US2: T019 (sw.js) e T020 (next.config) em paralelo com T015–T018.
- US3: o backend (T021–T024) e T025 em paralelo; T026–T028 depois de T025.
- US1 e US3 no backend são independentes e podem ser feitas em paralelo depois da fundação.

## Implementation Strategy

1. **MVP**: fazer Setup, Foundational e US1. A página `/lembretes` já responde "o que vence"
   sem nenhuma infraestrutura de push. É um bom ponto para validar e commitar.
2. **Push completo**: US2 e US3 juntas entregam a notificação de ponta a ponta. Fazer um commit
   para o backend do envio e outro para a ativação no frontend.
3. **Lembretes livres**: US4.
4. **Polish**: validar o quickstart e configurar o cron e as chaves em produção.
