# Research: Contas compartilhadas

## R1 — Como o lançamento do participante é criado sem violar o isolamento

**Decision** (revisada em 2026-10-16): a cota é gravada na cobrança (`cota_cobranca`), e o **lançamento previsto** é
materializado pelo **próprio participante** quando ele lê o seu ciclo: `materializar_cotas(db,
usuario_id, hoje, agora)`, idempotente (só cotas do usuário com `lancamento_id IS NULL`).

**Rationale**: o lançamento nasce sempre no `usuario_id` da cota e por ação do dono daquele
saldo (FR-004). Segue o padrão de `garantir_previstos_do_mes` (`services/recorrencia.py:96`), que
já gera previstos na leitura e dispensa cron. O dono também recebe o seu assim.

**Alternatives**: criar o lançamento de todos no ato da cobrança (mexe no ledger de terceiros e
falha para CLT sem ciclo aberto); cron diário (serviço extra, regra nova de deploy).

## R2 — Data e ciclo do lançamento da cota

**Decision**: data = vencimento da cobrança (`competencia` + `dia_vencimento`, ajustado ao último
dia do mês, como `no_mes` em `domain/recorrencia.py`). O lançamento só é criado se essa data cair
em um ciclo existente do participante na carteira PF (ciclo por salário ou por mês). Se ainda não
há ciclo que cubra a data, a cota espera (`lancamento_id` nulo) e é tentada de novo na próxima
leitura. Sempre `status = previsto`, `conta_no_saldo = True`, `carteira = pf`, categoria do
participante, descrição = descrição da conta.

**Rationale**: a regra "nenhum lançamento antes do primeiro salário" do CLT continua intacta.

## R3 — Quando materializar

**Decision**: no início das leituras de ciclo (`routes/ciclos.py`, mesmo ponto onde
`garantir_previstos_do_mes` já é chamado) e ao aceitar um convite. Uma consulta indexada por
`participante.usuario_id` com `lancamento_id IS NULL`; sem cotas pendentes, nada acontece.

**Alternatives**: materializar em toda rota (custo e acoplamento).

## R4 — Modos de divisão

**Decision**:
- `igual`: `dividir()` de `domain/parcelas.py:11` entre os participantes ativos; resto na
  última cota (ordem do `id` do participante).
- `percentual`: valores em pontos-base (bps) por participante, inclusive o dono, soma exata
  10000 entre os aceitos; cota = `total * bps // 10000`, resto na última.
- `fixo`: valor em centavos por participante, **inclusive o dono**; a soma entre os aceitos
  MUST ser igual ao total, senão 422 com a diferença.
O modo é da conta (todos os participantes seguem o mesmo).

**Rationale**: o resto sempre tem dono definido (última cota ou dono), garantindo soma == total
sem float.

## R5 — Convites e expiração

**Decision**: convite guarda `email_convite` normalizado (minúsculas) e `convidado_em`. Resposta
da API de convite é sempre a mesma (idêntica exista conta ou não). Expira 30 dias após
`convidado_em` (derivado na leitura, sem job). Ao cadastrar (`services/auth.py:43`), convites
pendentes não expirados daquele e-mail passam a apontar para o novo `usuario_id`. Usuário já
existente vê seus convites por e-mail igual ao do cadastro.

**Rationale**: evita enumerar e-mails; sem job de limpeza.

## R6 — Visibilidade e nome

**Decision**: `GET /{id}` devolve ao participante: descrição, total do mês, nº de pessoas,
`minha_cota`, e `outros: [{nome, status}]`. Nunca e-mail nem valor alheio. O dono vê, além
disso, e-mail do convite e valor de cada cota. O nome mostrado é o `usuario.nome`, ou o e-mail
convidado apenas para o dono quando o convite ainda está pendente.

## R7 — Admin e eventos

**Decision**: 5 eventos novos no `CHECK` (`conta_compartilhada_criada`, `convite_aceito`,
`convite_recusado`, `cobranca_gerada`, `cota_confirmada`), recriados na migração como a 0018.
Admin ganha contagem do módulo (contas, participantes aceitos) por usuário, sem nomes, e-mails
ou valores.

## R8 — Remoção e saída

**Decision**: `participante.status = 'removido'` (dono remove) ou `'saiu'` (participante sai);
nenhum lançamento ou cota existente muda (FR da clarificação). Novas cobranças ignoram quem não
está `aceito`. Excluir a conta é soft: `ativa = false`, sem apagar cobranças; lançamentos
realizados e previstos já materializados permanecem.

## R9 — Frontend

**Decision**: ler `node_modules/next/dist/docs/` antes de codar (`frontend/AGENTS.md`); página
de lista com convites pendentes no topo; página de detalhe com total, nº de pessoas, cota e
status; esconder o menu quando a carteira ativa for PJ.

## R10 — Quem gera a cobrança e quando (clarificação)

**Decision**: conta **sem** valor fixo: só o dono informa o total (`POST /{id}/cobrancas`); sem
total, o dono vê "falta informar o total de [mês]" (derivado: conta ativa sem cobrança da
competência atual). Conta **com** valor fixo: o dono pode gerar a cobrança quando quiser
(`POST /{id}/cobrancas` sem `valor_total`); se não gerar, `garantir_cobrancas_fixas` a gera a
partir do dia de vencimento da competência, na leitura de **qualquer** participante aceito, de
forma idempotente (UNIQUE conta + competência; conflito simultâneo tratado com `ON CONFLICT DO
NOTHING`). Assim o dono decide quando fechar a lista de aceitos.

## R11 — Divisor da cobrança (clarificação)

**Decision**: divide só entre participantes `aceito` na hora de gerar; o dono sempre conta. O
número de pessoas é o de aceitos; a API devolve também `qtd_convidados_pendentes`. Percentual e
fixo validam entre os aceitos na hora da cobrança (percentual soma 10000; fixos somam o total;
senão 422 com a diferença). O dono tem a própria parte e edita a de cada participante por
`PATCH /{id}/participantes/{participante_id}`. Quem
aceita depois entra só nas cobranças seguintes.

## R12 — Status da cota derivado (resolve conflito com a constituição)

**Decision**: a cota não guarda status. Guarda `confirmado_em` (dono). Status mostrado:
`pendente` (sem lançamento ou lançamento previsto), `informado` (lançamento realizado),
`confirmado` (`confirmado_em` preenchido e lançamento realizado). "Paguei" é o titular realizar
o próprio lançamento; "cancelar" é voltá-lo para previsto, o que invalida a confirmação.

**Rationale**: a constituição 8.1.0 proíbe que informar ou confirmar uma cota altere lançamento
ou saldo. Derivando o status do lançamento do próprio titular, nenhuma ação sobre a cota escreve
no ledger de ninguém.

**Alternatives**: coluna `status` na cota e uma ação que também realizava o lançamento (viola a
regra acima).

## R13 — Proteção do lançamento da cota

**Decision**: em `services/lancamento.py`, antes de excluir ou alterar `valor`/`data`, consultar
se existe `cota_cobranca.lancamento_id = :id`; se existir, 409 `lancamento_de_cota`. Também 409 ao alterar `carteira`, `conta_no_saldo` ou
`tipo`. Status (realizado/previsto), categoria e descrição seguem livres. Sem coluna nova em `lancamento`
(consulta, como `retirada_id` faz com `column_property`).

## R14 — Quem sai continua recebendo as cotas já geradas

**Decision**: `materializar_cotas` considera as cotas do usuário independentemente do status
atual do participante (`removido`/`saiu`); só a visão da conta some (404). Cobranças novas o
ignoram.

## R15 — Convite

**Decision**: `GET /convites` devolve `{id, titulo_conta, nome_do_dono, convidado_em}`, sem valores
nem e-mail. Aceitar define `usuario_id` e `categoria_id`. Rotas estáticas (`/convites`, `/cotas`)
declaradas antes das rotas com `{id}`.

## R16 — Lançamento travado de quem saiu

**Decision**: aceito no v1. O lançamento previsto da cota de quem saiu ou foi removido continua
travado (409 na exclusão), porque a cobrança já foi gerada e vale para os demais. Se virar
incômodo, uma exceção futura pode liberar a exclusão de previstos de quem saiu.
