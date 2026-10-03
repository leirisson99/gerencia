# Research: Carteiras PF e PJ (019)

Nenhum item ficou como NEEDS CLARIFICATION. As decisões abaixo saem do código atual e da
constituição 7.0.0.

## R1. Carteira como coluna, não como entidade

- **Decisão**: coluna `carteira` (`'pf'` | `'pj'`, `server_default 'pf'`, `CHECK`) em
  `lancamento` e `recorrencia`. Não existe tabela de carteira.
- **Rationale**: toda linha já existente vira PF sem migrar dados. Os 1052 testes atuais não
  informam carteira e continuam com o mesmo comportamento (SC-004). Uma tabela de carteiras
  seria uma entidade nova sem atributo próprio.
- **Alternativas**: tabela `carteira` com FK (sem ganho na fase 1); um usuário-sombra para a PJ
  (quebraria o isolamento e a autenticação).

## R2. Um único ponto decide o ciclo

- **Decisão**: função pura `domain/usuario.ciclo_pelo_mes(tipo_renda, carteira)`, que devolve
  `True` quando `carteira == "pj"` ou `tipo_renda == "prestador"`. As funções de
  `services/ciclo.py` (`ciclo_da_data_do_usuario`, `ciclo_atual_do_usuario`,
  `lancamentos_no_ciclo`, `primeira_data_lancamento`) ganham o parâmetro `carteira` com padrão
  `"pf"` e passam a filtrar por ele.
- **Rationale**: hoje `ciclo_da_data_do_usuario` já é o "único ponto que decide a regra".
  Estender a assinatura com padrão `"pf"` mantém todos os chamadores atuais corretos.
- **Alternativas**: um service paralelo para a PJ (duplicaria a regra de ciclo).

## R3. Cobertura por salário só olha a PF

- **Decisão**: `datas_de_salario` e `menor_data_dos_outros` filtram `carteira = 'pf'`. Isso
  vale para lançamento, importação, perfil (troca de tipo) e exclusão ou mudança de salário.
- **Rationale**: FR-005. Um lançamento PJ nunca pode bloquear nem ser bloqueado pelo salário.
- **Risco**: uma consulta sem o filtro faria a PJ exigir salário. Haverá teste explícito para
  `clt_prestador` sem salário lançando na PJ e trocando de tipo com dados PJ.

## R4. Retirada: tabela dona dos dois lados

- **Decisão**: tabela `retirada` (`usuario_id`, `data`, `valor`, `lancamento_pj_id` e
  `lancamento_pf_id` únicos, `criado_em`). Criar, editar e excluir passam por
  `services/retirada.py` numa transação. `lancamento.editar_lancamento` e `excluir_lancamento`
  recusam com 409 `lancamento_de_retirada` quando o lançamento é lado de uma retirada (mesmo
  padrão de `deposito_de_cartela`, `parcela_de_divida` e `lancamento_de_servico`).
- **Rationale**: a regra "editados e excluídos só juntos" (princípio I) fica num lugar. Como os
  lados são lançamentos comuns, saldo, gasto e lembretes funcionam sem caso especial.
- **Alternativas**: coluna `par_id` em `lancamento` (a dona da regra ficaria implícita);
  `conta_no_saldo = False` nos lados (errado: a retirada de fato tira dinheiro da PJ e põe na
  PF).

## R5. Categorias de sistema da PJ

- **Decisão**: ao ligar a PJ, garantir "Retirada para PF" (saída) e "Pró-labore e lucros"
  (entrada), ambas com `sistema = True`, de forma idempotente. Se o usuário já tiver uma
  categoria com o mesmo nome (sem diferenciar maiúsculas) e o mesmo tipo, ela é promovida a
  sistema. Com tipo diferente, ligar a PJ responde 409 `categoria_conflitante`, pedindo que ele
  renomeie a categoria. Desligar a PJ mantém as categorias.
- **Rationale**: o nome é único por usuário (índice existente). Promover evita duplicar o que o
  usuário já criou para o mesmo fim.

## R6. Recorrências por carteira

- **Decisão**: `gerar_previstos` recebe a carteira e só usa as recorrências dela.
  - Salário PF que abre ciclo → só as recorrências PF.
  - `garantir_previstos_do_mes(db, usuario_id, hoje, agora, carteira)`: idempotente. Na PJ
    roda sempre; na PF, só se o tipo for `prestador` (comportamento atual).
  - Criar recorrência com ciclo aberto gera o previsto do ciclo da carteira dela.
- **Rationale**: FR-011. Reaproveita a idempotência que já existe (um previsto por recorrência
  dentro do ciclo).

## R7. Carteira nas rotas de leitura e escrita

- **Decisão**:
  - Leitura: `?carteira=pf|pj` (padrão `pf`) nas 4 rotas de ciclo.
  - Escrita: o campo `carteira` é opcional em `LancamentoIn` e `RecorrenciaIn`, e o `PATCH` de
    lançamento aceita mudar a carteira.
  - `LancamentoOut` e `RecorrenciaOut` passam a trazer `carteira`.
  - Pedir ou gravar PJ com a PJ desligada responde 409 `carteira_pj_desligada`.
- **Rationale**: aditivo, e os clientes atuais seguem funcionando.

## R8. Lembretes

- **Decisão**: `ItemLembrete` ganha `carteira` (`pf` | `pj`; lembrete livre = `pf`). A janela e
  a regra não mudam. O push conta os dois juntos.

## R9. Seletor no frontend

- **Decisão**: o cookie `carteira` (`pf` | `pj`) é lido pelos server components e enviado como
  `?carteira=` à API. O seletor no `app-shell` grava o cookie e chama `router.refresh()`. Sem a
  PJ ligada, o cookie é ignorado e vale `pf`.
- **Rationale**: a escolha precisa valer em todas as telas (início, lançamentos, calendário,
  recorrências) sem levar um parâmetro em cada link. É conveniência por navegador: perder o
  cookie só volta para a PF.
- **Alternativas**: parâmetro na URL (todo link interno teria de propagá-lo); preferência
  salva no usuário (gravaria estado de interface no banco).

## R10. Perfil e troca de tipo de renda

- **Decisão**: `PATCH /me` aceita `tem_pj`. Ligar exige `prestador` ou `clt_prestador`.
  Desligar, ou trocar para `clt`, é recusado com 409 `pj_com_dados` se houver lançamento,
  recorrência ou retirada PJ. Trocar para `clt` sem dados PJ desliga a PJ junto. Essa
  verificação fica numa função pura em `domain/usuario.py`, ao lado de
  `verificar_troca_tipo_renda`.

## R11. Administrador

- **Decisão**:
  - Eventos novos `retirada_feita`, `retirada_editada` e `retirada_excluida`.
  - `ContagensContaOut` ganha `retiradas`, e os lados da retirada contam em
    `lancamentos_gerados`.
  - O detalhe não mostra carteira nem valores.

## R12. Migração

- **Decisão**: `0018_carteira_pj.py`:
  - `usuario.tem_pj`;
  - `carteira` em `lancamento` e `recorrencia`, com troca do índice
    `ix_lancamento_usuario_data` por `(usuario_id, carteira, data)`;
  - a tabela `retirada`;
  - o `CHECK` de `evento_uso` com os 3 tipos novos.
  Downgrade só com a base sem dados PJ (apaga as retiradas e recusa se houver PJ).
