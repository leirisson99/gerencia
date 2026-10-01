# Contrato: Lembretes por Push

Mesmas regras das features anteriores:

- cookie `sessao`;
- formato único de erro;
- valores em centavos inteiros.

As rotas exigem sessão e troca de senha em dia. O administrador é tratado como nas demais rotas
financeiras: não tem lançamentos, e o envio do resumo o ignora. Nenhuma rota existente muda.

## Lembretes

### Tipos

```json
// LembreteLivreOut
{ "id": 4, "texto": "Renovar o seguro do carro", "data": "2026-10-12",
  "concluido": false, "concluido_em": null, "criado_em": "2026-10-01T12:00:00Z" }

// ItemLembrete: um lançamento previsto ou um lembrete livre
{ "origem": "conta",                 // "conta" | "valor" | "livre"
  "situacao": "a_vencer",            // "atrasado" | "a_vencer"
  "data": "2026-10-12",
  "lancamento": { /* LancamentoOut */ },  // em "conta" e "valor"; null em "livre"
  "lembrete": null }                 // LembreteLivreOut em "livre"; null nos outros

// LembretesOut
{ "hoje": "2026-10-10", "limite": "2026-10-13",
  "atrasados": [ /* ItemLembrete, por data e id */ ],
  "a_vencer":  [ /* ItemLembrete, por data e id */ ] }
```

### Rotas

| Método e caminho | Corpo | Resposta |
| --- | --- | --- |
| `GET /api/v1/lembretes` | — | `LembretesOut` (só a janela; derivado na hora) |
| `GET /api/v1/lembretes/livres` | — | `LembreteLivreOut[]`, todos os lembretes livres, por `data`, `id` |
| `POST /api/v1/lembretes/livres` | `LembreteLivreIn` | 201 `LembreteLivreOut` |
| `PATCH /api/v1/lembretes/livres/{id}` | `LembreteLivrePatch` | `LembreteLivreOut` |
| `DELETE /api/v1/lembretes/livres/{id}` | — | 204 |

- `LembreteLivreIn`: `texto` (obrigatório, até 200 caracteres) e `data`. Campos extras são
  recusados.
- `LembreteLivrePatch`: `texto?`, `data?`, `concluido?: bool`. `null` em qualquer campo dá 422.

### Erros

- 404 `nao_encontrado` ("Lembrete não encontrado."): o lembrete não existe ou é de outro
  usuário.
- 422 `validacao`: aponta o campo (`texto` vazio ou longo, `data` ausente ou inválida).

## Push

### Rotas

| Método e caminho | Corpo | Resposta |
| --- | --- | --- |
| `GET /api/v1/push/chave` | — | `{ "chave_publica": "<base64url>" }` |
| `PUT /api/v1/push/inscricao` | `InscricaoIn` | 204 (cria ou transfere para quem chamou) |
| `DELETE /api/v1/push/inscricao` | `{ "endpoint": "..." }` | 204 |

- `InscricaoIn`: `{ "endpoint": "https://...", "keys": { "p256dh": "...", "auth": "..." } }`.
  É o formato de `PushSubscription.toJSON()`; o campo `expirationTime` é aceito e ignorado.

### Erros

- 503 `push_indisponivel` ("As notificações não estão disponíveis no momento."): chaves VAPID não
  configuradas. Vale para `GET /push/chave` e `PUT /push/inscricao`.
- 404 `nao_encontrado` no `DELETE`: o endpoint não está inscrito por quem chamou.
- 422 `validacao`: endpoint que não é `https://` ou passa de 2048 caracteres, ou chaves
  ausentes.

## Comandos de servidor

| Comando | Efeito | Saída |
| --- | --- | --- |
| `python -m app.cli enviar-lembretes` | Envia o resumo do dia em `America/Sao_Paulo`. Idempotente no mesmo dia. | Uma linha só com contagens: `usuarios=… enviados=… sem_pendencias=… ja_enviados=… removidos=… falhas=…`. Código 0, ou 1 se o push não estiver configurado. |
| `python -m app.cli gerar-chaves-vapid` | Gera um par de chaves. | `VAPID_CHAVE_PUBLICA=…` e `VAPID_CHAVE_PRIVADA=…`, para copiar para o `.env`. |

Variáveis de ambiente:

- `VAPID_CHAVE_PUBLICA` e `VAPID_CHAVE_PRIVADA`, em base64url;
- `VAPID_CONTATO`, com `mailto:` ou URL, que vai no claim `sub`.

## Notificação (payload do push)

```json
{ "titulo": "Gerencia",
  "corpo": "2 contas a pagar até sábado · 1 valor a receber, atrasado.",
  "url": "/lembretes" }
```

- O envio usa TTL de 43200 s (12 h) e urgência `normal`.
- O service worker mostra a notificação com `tag: "lembretes"`, de modo que a nova substitui a
  anterior.
- Ao tocar, abre `url`.
