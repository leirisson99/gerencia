# Research: Lembretes por Push

## 1. Biblioteca de Web Push no backend

- **Decision**: `pywebpush` 2.5 (requer Python ≥ 3.10; traz `py-vapid` e `cryptography`).
  Chamada síncrona `webpush(subscription_info, data, vapid_private_key, vapid_claims, ttl=...)`;
  recusa do serviço de push vem como `WebPushException` com `response.status_code`.
- **Rationale**: é a implementação de referência em Python do protocolo (RFC 8030, 8291 e 8292),
  mantida pela Mozilla; criptografa o payload ponta a ponta, então o serviço de push (Google,
  Apple, Mozilla) não lê o conteúdo.
- **Alternatives considered**: implementar RFC 8291 à mão (arriscado, criptografia); enviar pelo
  Next com `web-push` (Node), como no guia do Next — exigiria que o frontend lesse o banco ou
  recebesse as pendências, quebrando "o frontend consome só a API".

## 2. Onde rodar o envio diário

- **Decision**: subcomando `enviar-lembretes` do `app.cli`, agendado pelo cron do servidor às
  11:00 UTC (8h em São Paulo; sem horário de verão desde 2019). Ex.:
  `0 11 * * * docker compose exec -T api python -m app.cli enviar-lembretes`.
- **Rationale**: a constituição exige comando agendado fora das requisições; reaproveita models,
  services e banco; o cron do sistema é o agendador mais simples e observável.
- **Alternatives considered**: APScheduler dentro da API (duplica com vários workers e morre com
  o processo); fila (Celery/RQ) — serviço extra sem necessidade (Princípio VI).

## 3. No máximo um resumo por dia

- **Decision**: tabela `envio_lembrete (usuario_id, dia)` com chave única. O envio reserva o dia
  com `INSERT ... ON CONFLICT DO NOTHING RETURNING` e commit antes de enviar; se nenhum aparelho
  aceitou, apaga a reserva.
- **Rationale**: garante a unicidade mesmo com duas execuções simultâneas (cron duplicado,
  execução manual) e permite nova tentativa em falha total (edge case da spec).
- **Alternatives considered**: coluna `ultimo_envio` em `usuario` (corrida entre execuções sem
  lock); marcar depois de enviar (duas execuções simultâneas enviam duas vezes).

## 4. Identidade do aparelho e troca de usuário

- **Decision**: `inscricao_push.endpoint` único em toda a tabela. `PUT /push/inscricao` faz upsert
  pelo endpoint e atribui ao usuário autenticado, atualizando as chaves.
- **Rationale**: o endpoint é o identificador natural do aparelho/navegador no Web Push; ser
  único garante FR-008 (um aparelho, um usuário) sem lógica extra.
- **Alternatives considered**: chave `(usuario_id, endpoint)` — o mesmo aparelho receberia o
  resumo de duas contas depois de uma troca de usuário.

## 5. Sair da conta

- **Decision**: o frontend, antes do logout, chama `DELETE /push/inscricao` com o endpoint do
  aparelho e `subscription.unsubscribe()`; falhas não impedem o logout.
- **Rationale**: só o navegador conhece o próprio endpoint; ligar a inscrição à sessão faria o
  push parar quando a sessão expira por 30 dias sem uso — justamente quem depende do lembrete.
- **Alternatives considered**: `inscricao_push.sessao_id` com cascade (para de lembrar quem não
  abre o app); não fazer nada ao sair (viola FR-008).

## 6. Chave pública VAPID no frontend

- **Decision**: `GET /api/v1/push/chave` devolve a chave pública configurada no backend; 503
  `push_indisponivel` sem chaves.
- **Rationale**: uma única fonte das chaves (variáveis do backend); trocar as chaves não exige
  rebuild do frontend; o frontend sabe esconder a ativação quando o push está desligado.
- **Alternatives considered**: `NEXT_PUBLIC_VAPID_PUBLIC_KEY` no build do frontend (duas fontes
  que podem divergir).

## 7. Service worker

- **Decision**: arquivo estático `frontend/public/sw.js`, registrado com `scope: "/"` e
  `updateViaCache: "none"`; `next.config.ts` serve `/sw.js` com `Cache-Control: no-cache`.
  Trata só `push` (mostra a notificação com `tag: "lembretes"`) e `notificationclick` (foca uma
  janela aberta do app ou abre `/lembretes`). Sem cache offline.
- **Rationale**: o guia de PWA do Next 16 (`node_modules/next/dist/docs/01-app/02-guides/
  progressive-web-apps.md`) usa um service worker simples; arquivo em `public/` evita depender
  do bundler para um script que roda fora da página.
- **Alternatives considered**: next-pwa/Serwist (cache offline fora do escopo, dependência a
  mais).

## 8. Suporte e iPhone

- **Decision**: o Perfil detecta `"serviceWorker" in navigator && "PushManager" in window`,
  `Notification.permission` e, no iOS, se o app está instalado
  (`matchMedia("(display-mode: standalone)")` ou `navigator.standalone`). Estados: ativo, inativo,
  bloqueado, iPhone sem instalar, sem suporte, indisponível no servidor.
- **Rationale**: FR-017; iOS só expõe `PushManager` no app instalado (16.4+).

## 9. Texto do resumo

- **Decision**: título fixo "Gerencia"; corpo com até três partes separadas por " · ", só com
  contagens e o dia da semana do fim da janela (regras em [data-model.md](data-model.md)).
- **Rationale**: FR-010/SC-003 — testável em função pura; a tela bloqueada não revela valores,
  descrições, categorias, nomes nem o texto dos lembretes livres.
