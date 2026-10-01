# Quickstart: Lembretes por Push

## Preparação

```bash
# backend/, com Docker Desktop aberto
docker compose up -d db
uv sync
uv run alembic upgrade head            # cria lembrete, inscricao_push, envio_lembrete
uv run python -m app.cli gerar-chaves-vapid   # copie a saída para o .env
# .env: VAPID_CHAVE_PUBLICA=…, VAPID_CHAVE_PRIVADA=…, VAPID_CONTATO=mailto:voce@exemplo.com
uv run uvicorn app.main:app --reload

# frontend/
npm run dev
```

O push exige HTTPS, com uma exceção: `http://localhost` vale como contexto seguro. No celular,
use o app publicado em HTTPS. No iPhone, adicione o app à tela inicial antes.

## Testes automatizados

```bash
uv run pytest tests/domain/test_lembrete.py tests/api/test_lembretes.py \
  tests/api/test_push.py tests/services/test_envio_lembrete.py tests/api/test_isolamento.py
uv run pytest && uv run ruff check . && uv run ruff format --check .
# frontend/
npm run lint && npm run build
```

## Cenários de validação

1. **Janela** (US1):
   - Lance saídas previstas com datas ontem, hoje, hoje + 3 e hoje + 4.
   - Esperado em `GET /api/v1/lembretes`: ontem em `atrasados`, hoje e hoje + 3 em `a_vencer`, e
     hoje + 4 em nenhuma das duas.
   - Uma parcela paga no cartão não aparece.
2. **Valores a receber** (US1): um serviço com data prevista para amanhã aparece em `a_vencer`
   com `origem: "valor"`.
3. **Ativar** (US3): no Perfil, clique em "Ativar notificações" e autorize no navegador. O Perfil
   passa a mostrar "ativadas neste aparelho".
4. **Envio** (US2):
   - Rode `uv run python -m app.cli enviar-lembretes`. Chega uma notificação só com contagens, e
     tocar nela abre `/lembretes`.
   - Rode de novo: a saída mostra `ja_enviados=1` e nenhuma notificação nova chega.
5. **Sem pendências** (US2): um usuário sem nada na janela não recebe notificação
   (`sem_pendencias`).
6. **Aparelho revogado** (US2): bloqueie as notificações do site no navegador e rode o envio do
   dia seguinte (ou apague a linha de `envio_lembrete`). A inscrição é removida (`removidos=1`).
7. **Sair** (US3): saia da conta e rode o envio. O aparelho não recebe.
8. **Lembrete livre** (US4):
   - Crie "renovar seguro" para depois de amanhã: aparece em `a_vencer` e conta no resumo.
   - Conclua: some da janela e continua em `GET /lembretes/livres` com `concluido: true`.
9. **Isolamento**: com outra conta, `PATCH /api/v1/lembretes/livres/{id}` num lembrete da
   primeira conta retorna 404.

## Produção (Easypanel)

1. **Chaves:** gere um par só para produção com `uv run python -m app.cli gerar-chaves-vapid`.
   No serviço da API, em **Environment**, cadastre `VAPID_CHAVE_PUBLICA`,
   `VAPID_CHAVE_PRIVADA` e `VAPID_CONTATO`. Gere uma vez só: trocar as chaves obriga todo mundo a
   ativar as notificações de novo.
2. **Serviço `lembretes`:** crie um novo serviço de app no mesmo projeto, com o mesmo
   repositório e a mesma branch da API.
   - Build: Dockerfile `backend/Dockerfile.cron`, com a raiz do repositório como contexto (igual
     à API).
   - Environment: as mesmas `DATABASE_URL` e `VAPID_*` da API.
   - Sem domínio e sem porta: o serviço não recebe requisições.
3. **Deploy:** faça o deploy da API primeiro, porque ela aplica as migrações, e depois o do
   `lembretes`.
4. **Conferir:** nos logs do `lembretes`, o supercronic mostra a execução das 11:00 UTC (8h em
   São Paulo) e a linha de contagens (`usuarios=… enviados=…`). Para testar fora do horário, use
   o console do serviço e rode `python -m app.cli enviar-lembretes`.

O agendamento fica em `backend/crontab`. O comando não reenvia no mesmo dia, então rodar mais
de uma vez é seguro.
