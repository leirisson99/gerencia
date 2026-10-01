# Implementation Plan: Lembretes por Push

**Branch**: `015-lembretes-push` | **Date**: 2026-10-01 | **Spec**: [spec.md](spec.md)

## Summary

Contas a pagar e valores a receber são uma consulta aos lançamentos previstos com
`data <= hoje + 3`, classificados por uma função pura em `domain/lembrete.py` (atrasado ou a
vencer), que também monta o texto do resumo só com contagens. Lembretes livres ganham a tabela
`lembrete`. Cada aparelho autorizado vira uma linha em `inscricao_push`, com o endpoint único
(ativar em outra conta transfere a linha). O comando `python -m app.cli enviar-lembretes`,
agendado por cron às 8h de São Paulo, percorre os usuários ativos com aparelhos, reserva o dia em
`envio_lembrete` (única por usuário e dia) antes de enviar, envia por Web Push (VAPID, com
`pywebpush`), remove aparelhos recusados (404/410) e libera a reserva se nenhum aparelho
recebeu. No frontend: service worker em `public/sw.js`, seção de notificações no Perfil, página
`/lembretes` e desinscrição do aparelho ao sair.

## Technical Context

**Language/Version**: Python 3.14 (backend); TypeScript, Next.js 16 e React 19 (frontend)

**Primary Dependencies**: as mesmas, mais `pywebpush` (2.5, traz `py-vapid`), permitido pela
constituição 5.1.0

**Storage**: PostgreSQL 17, com as tabelas `lembrete`, `inscricao_push` e `envio_lembrete`
(migração `0015`)

**Testing**:

- `tests/domain/test_lembrete.py`: janela, situação, contagem e texto do resumo.
- `tests/api/test_lembretes.py` e `tests/api/test_push.py`: rotas e isolamento.
- `tests/services/test_envio_lembrete.py`: envio com um enviador falso, sem rede.
- Ajuste em `tests/api/test_isolamento.py`.

**Target Platform**: servidor Linux (API e cron); navegadores com Web Push (Chromium, Firefox,
Safari 16+, iOS 16.4+ instalado)

**Project Type**: web service + frontend web (PWA)

**Performance Goals**:

- O resumo de todos os usuários termina em minutos, para chegar até as 8h30 (SC-004).
- Uma consulta de pendências por usuário com aparelho; o volume é pequeno.

**Constraints**:

- O envio nunca roda em requisição (FR-015).
- A notificação só leva contagens (FR-010).
- Logs do envio só com contagens (FR-018).
- Push desligado, sem erro de inicialização, quando as chaves VAPID não estão configuradas.

**Scale/Scope**: dezenas a centenas de usuários; poucos aparelhos por usuário

## Constitution Check

| Princípio | Verificação | Status |
| --- | --- | --- |
| I. Integridade financeira | Nada novo entra no saldo. Lembretes só leem lançamentos; os valores mostrados na página são `int` em centavos vindos do lançamento. | ✅ |
| II. Ciclo | A janela usa a data de hoje em `America/Sao_Paulo`, passada como parâmetro, e não depende de ciclo. Nada de ciclo é guardado. | ✅ |
| III. Teste primeiro | Os testes de `domain/lembrete.py` vêm antes: ontem, hoje, hoje + 3 e hoje + 4; plural e singular; resumo vazio. O envio é testado com um enviador falso, cobrindo 404/410, falha total e reexecução no mesmo dia. | ✅ |
| IV. Contratos | Schemas tipados ([contracts/api.md](contracts/api.md)) e erros no formato único. As mudanças são só aditivas; nenhuma rota existente muda. | ✅ |
| V. Isolamento | `lembrete` e `inscricao_push` têm `usuario_id`, e as consultas filtram por ele. Lembrete de outro usuário retorna 404, com teste. As chaves VAPID ficam em variáveis de ambiente, e os logs não levam endpoint nem conteúdo. | ✅ |
| VI. Escopo | Cumpre as regras de lembretes da 5.1.0: três origens, janela de 3 dias, contas e valores derivados, resumo diário único sem valores nem nomes, envio por comando agendado. O comando é do próprio monólito (justificado em Decisões), sem fila nem serviço extra. | ✅ |

**Resultado**: sem violações. Reavaliado depois do desenho: sem mudanças.

## Project Structure

### Documentation

```text
specs/015-lembretes-push/
├── plan.md, research.md, data-model.md, quickstart.md
├── contracts/api.md
└── tasks.md            # /speckit-tasks
```

### Source Code

```text
backend/
├── alembic/versions/0015_lembretes_push.py
├── app/config.py                    # + vapid_chave_publica, vapid_chave_privada, vapid_contato
├── app/domain/lembrete.py           # situacao, contar, texto_resumo (puras)
├── app/models/lembrete.py           # Lembrete, InscricaoPush, EnvioLembrete
├── app/schemas/lembrete.py          # LembretesOut, ItemLembrete, LembreteLivreIn/Patch/Out
├── app/schemas/push.py              # ChavePushOut, InscricaoIn, InscricaoRemoverIn
├── app/services/lembrete.py         # pendências do usuário e CRUD de lembretes livres
├── app/services/push.py             # inscrever (upsert/transferência) e remover
├── app/services/envio_lembrete.py   # enviar_lembretes_do_dia(db, hoje, enviador)
├── app/push.py                      # adaptador do pywebpush (infra)
├── app/api/routes/lembretes.py
├── app/api/routes/push.py
├── app/cli.py                       # + enviar-lembretes, gerar-chaves-vapid
├── app/main.py                      # include_router
└── tests/domain/test_lembrete.py, tests/api/test_lembretes.py, tests/api/test_push.py,
    tests/services/test_envio_lembrete.py

frontend/
├── public/sw.js                     # push e notificationclick
├── next.config.ts                   # cabeçalhos de /sw.js
├── lib/push.ts                      # suporte, registro, ativar, desativar, sincronizar
├── lib/api/lembretes.ts, lib/api/push.ts, lib/api/types.ts, lib/api/server.ts
├── features/perfil/secao-notificacoes.tsx
├── features/lembretes/              # lista, dialog do lembrete livre
├── features/auth/use-sair.ts        # desinscreve o aparelho antes de sair
├── components/layout/app-sidebar.tsx  # item "Lembretes"
└── app/(app)/lembretes/page.tsx
```

**Structure Decision**: monólito FastAPI e frontend Next, como nas features anteriores. A regra
pura fica em `domain/lembrete.py`. O envio fica em `services/`, com o transporte injetado para
o teste não depender de rede.

## Decisões

Detalhes e alternativas em [research.md](research.md).

- **Pendências**: uma consulta a `lancamento` com `status = previsto`, `data <= hoje + 3` e
  (`tipo = entrada` ou `conta_no_saldo`), ordenada por data e id. Os lembretes livres não
  concluídos entram na mesma janela. Nada é guardado.
- **Aparelho**: identificado pelo `endpoint` do Web Push, que é único. `PUT` faz upsert: se o
  endpoint já é de outro usuário, a linha passa para quem chamou (FR-008). O frontend chama `PUT`
  de novo ao abrir o Perfil para sincronizar.
- **Sair**: o frontend remove a inscrição na API e no navegador antes do logout. O servidor não
  liga a inscrição à sessão, porque a sessão expira por inatividade e o push deve continuar.
- **Envio único por dia**: `INSERT ... ON CONFLICT DO NOTHING RETURNING` em `envio_lembrete`
  reserva o dia antes de enviar. Isso cobre duas execuções simultâneas. Se nenhum aparelho
  recebeu, a reserva é apagada e a próxima execução do dia tenta de novo.
- **Monólito**: o envio é um subcomando do `app.cli`, com o mesmo código e banco, disparado pelo
  cron do servidor. Um agendador dentro da API duplicaria o envio com vários workers.
- **Chave pública**: servida por `GET /push/chave`, para o frontend não precisar de rebuild ao
  trocar as chaves. Sem chaves configuradas, a rota responde 503 `push_indisponivel` e o Perfil
  esconde a ativação.
- **Notificação**: payload `{titulo, corpo, url: "/lembretes"}`, TTL de 12 h e `tag` fixa, para
  um resumo novo substituir o antigo no aparelho.

## Complexity Tracking

Sem violações.
