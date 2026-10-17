# Data Model: Contas compartilhadas

Valores em centavos (`BigInteger`). Constraints no padrão `ck_`, `uq_`, `fk_` de
`app/models/__init__.py`.

## conta_compartilhada

| Campo | Tipo | Regra |
| --- | --- | --- |
| id | BigInteger Identity | PK |
| dono_id | FK usuario (CASCADE) | quem cadastrou; único que edita |
| categoria_id | FK categoria (RESTRICT) | categoria do dono para a cota dele |
| descricao | String(200) | ex.: "Energia" |
| modo | String(10) | `igual` \| `percentual` \| `fixo` (CHECK) |
| dia_vencimento | SmallInteger | 1 a 31 (CHECK) |
| valor_fixo | BigInteger null | total mensal fixo (aluguel); NULL = informar por mês; > 0 |
| ativa | bool | padrão true |
| criado_em | DateTime tz | |

Índice `(dono_id)`.

## participante_conta

| Campo | Tipo | Regra |
| --- | --- | --- |
| id | BigInteger Identity | PK; ordem define "última cota" |
| conta_id | FK conta_compartilhada (CASCADE) | |
| usuario_id | FK usuario (CASCADE) null | nulo até o e-mail se cadastrar; o dono tem o seu desde o início |
| email_convite | String(254) null | normalizado; nulo para o dono |
| status | String(10) | `pendente` \| `aceito` \| `recusado` \| `removido` \| `saiu` (CHECK); aceitar define `usuario_id` e `categoria_id` |
| categoria_id | FK categoria null | escolhida ao aceitar |
| valor | BigInteger null | bps (percentual) ou centavos (fixo); nulo em igual |
| eh_dono | bool | exatamente um por conta |
| convidado_em | DateTime tz | base dos 30 dias |

UNIQUE `(conta_id, usuario_id)` e `(conta_id, email_convite)` onde não nulos (parciais).
Limite de 20 participantes ativos (`pendente` + `aceito`) por conta, validado no service dentro
de transação com trava da conta (não é CHECK do banco).

## cobranca_mensal

| Campo | Tipo | Regra |
| --- | --- | --- |
| id | BigInteger Identity | PK |
| conta_id | FK (CASCADE) | |
| competencia | Date | dia 1 do mês |
| valor_total | BigInteger | > 0 |
| criado_em | DateTime tz | |

UNIQUE `(conta_id, competencia)`.

## cota_cobranca

| Campo | Tipo | Regra |
| --- | --- | --- |
| id | BigInteger Identity | PK |
| cobranca_id | FK (CASCADE) | |
| participante_id | FK participante_conta (RESTRICT) | |
| valor | BigInteger | >= 0 |
| lancamento_id | FK lancamento (RESTRICT) null | só do próprio usuário da cota; nulo até materializar |
| confirmado_em | DateTime tz null | preenchido pelo dono; vale só enquanto o lançamento estiver realizado |
| atualizado_em | DateTime tz | |

Status mostrado (derivado, nunca armazenado): `pendente` (sem lançamento ou previsto),
`informado` (lançamento realizado), `confirmado` (`confirmado_em` e lançamento realizado).

UNIQUE `(cobranca_id, participante_id)`; índice parcial `(participante_id) WHERE
lancamento_id IS NULL` para a materialização. Soma das cotas de uma cobrança == `valor_total`
(garantida pelo domínio e testada).

## Transições

- Participante: `pendente → aceito | recusado`; `aceito → removido | saiu`; convite expirado
  (derivado, 30 dias) não aceita mais.
- Cota (derivada): `pendente → informado` quando o titular realiza o próprio lançamento;
  `informado → confirmado` quando o dono confirma; cancelar (lançamento volta a previsto) leva
  a `pendente` e invalida a confirmação. Confirmar e desfazer a confirmação não mexem em
  lançamento.

## Não muda

`lancamento`, `divida`, `recorrencia`, `categoria`, `usuario`: nenhuma coluna nova.
Cadastro (`services/auth.py`) só ganha o vínculo de convites pendentes.
