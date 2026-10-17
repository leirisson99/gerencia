# Contrato: contas compartilhadas (020)

Prefixo `/api/v1/contas-compartilhadas`. Todas exigem login. Mudanças aditivas; nenhuma rota
existente muda de formato. Conta fora do acesso (não dono, não participante aceito) → 404
`nao_encontrado`. **Ordem no código**: rotas estáticas (`/convites`, `/cotas/...`) antes das
com `{id}`.

## Erros novos (formato `ErroOut`)

| Status | Código | Quando |
| --- | --- | --- |
| 403 | `somente_dono` | participante tenta editar conta, convidar, gerar cobrança ou confirmar |
| 409 | `limite_participantes` | passa de 20 participantes (dono incluído) |
| 409 | `convite_expirado` | aceitar convite com mais de 30 dias |
| 409 | `cobranca_ja_gerada` | cobrança da competência já existe |
| 409 | `lancamento_de_cota` | excluir, ou alterar valor ou data, do lançamento de uma cota |
| 409 | `cota_nao_informada` | dono confirma cota cujo lançamento não está realizado |
| 422 | `validacao` | percentual ≠ 100%, fixos ≠ total, valor ≤ 0 (entre os aceitos, na cobrança; devolve a diferença) |

## Convites (participante)

- `GET /convites` — convites pendentes e não expirados do e-mail do usuário:
  `{id, descricao_conta, nome_do_dono, convidado_em}`. Sem valores nem e-mail.
- `POST /convites/{participante_id}/aceitar` — `{categoria_id}`; define `usuario_id` e
  categoria. `POST .../recusar`.

## Cotas

- `POST /cotas/{cota_id}/confirmar` e `POST /cotas/{cota_id}/desfazer-confirmacao` — dono.
  Gravam só `confirmado_em`; exigem lançamento realizado (409 `cota_nao_informada`) e nunca
  escrevem em lançamento.
- O titular "paga" e "cancela" pelo endpoint de lançamento já existente
  (`PATCH /api/v1/lancamentos/{id}`, `status` realizado ↔ previsto); não há rota de cota para
  isso.

## Dono

- `POST /` — cria conta `{descricao, categoria_id, modo, dia_vencimento, valor_fixo?}` (o dono entra
  como participante aceito). `GET /` lista as contas (dono e participante) com `valor_total` do
  mês, `qtd_pessoas` (aceitos), `qtd_convidados_pendentes`, `minha_cota` e, para o dono,
  `falta_informar_total` (conta variável sem cobrança do mês).
- `GET /{id}` — detalhe do dono: total do mês, aceitos e pendentes, cota e status de cada um
  (derivados), e-mails de convite.
- `PATCH /{id}` — altera descrição, categoria, dia, valor fixo, modo, `ativa`. Não muda cobranças já
  geradas.
- `POST /{id}/participantes` — `{email, valor?}`. Resposta idêntica exista conta ou não.
- `PATCH /{id}/participantes/{participante_id}` — `{valor}` (bps no percentual, centavos no
  fixo); vale para o dono também (`participante_id` do dono). Não muda cobranças já geradas.
- `DELETE /{id}/participantes/{participante_id}` — remove (vale da próxima cobrança; cotas já
  geradas continuam virando lançamento para ele).
- `POST /{id}/cobrancas` — `{competencia, valor_total?}`; `valor_total` obrigatório em conta
  sem valor fixo; em conta com `valor_fixo` o dono pode gerar quando quiser, e se não gerar a
  cobrança nasce sozinha a partir do dia de vencimento, na leitura de qualquer participante
  aceito. Divide só entre os aceitos.

## Participante

- `GET /{id}` — visão do participante: descrição, total do mês, `qtd_pessoas` (aceitos),
  `qtd_convidados_pendentes`, `minha_cota` (valor e status derivado) e
  `outros: [{nome, status}]`. Sem e-mail e sem valor alheio.
- `POST /{id}/sair`.

## Leitura do ciclo

`GET /api/v1/ciclos/atual` e demais leituras de ciclo passam a, de forma idempotente: gerar
cobranças de contas com valor fixo e materializar os previstos das cotas do próprio usuário
(sem mudar o formato da resposta).

## Lançamentos (rota existente)

`DELETE /api/v1/lancamentos/{id}` e `PATCH` de `valor`, `data`, `carteira`, `conta_no_saldo`
ou `tipo` devolvem 409 `lancamento_de_cota` quando o lançamento é de uma cota. `status`,
categoria e descrição seguem permitidos.
