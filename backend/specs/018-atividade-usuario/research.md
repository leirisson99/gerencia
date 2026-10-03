# Research: Atividade do Usuário (018)

Nenhum item ficou como NEEDS CLARIFICATION no contexto técnico. As decisões abaixo saem do código
atual e da constituição 6.0.0.

## R1. Onde registrar o evento de uso

- **Decisão**: dentro das funções públicas dos `services/` (`criar_lancamento`,
  `importacao.confirmar`, `cartela.depositar` etc.), por um único helper
  `services/evento_uso.registrar(db, usuario_id, tipo)` que só faz `db.add` antes do `commit`
  que a função já faz.
- **Rationale**: evento e ação caem na mesma transação. Se a ação falha (`ErroApi`, rollback),
  o evento também não fica (FR-006). Essas funções só são chamadas pelas rotas, nunca por
  outros services, então cada ação gera exatamente um evento: a importação não passa por
  `criar_lancamento`, e os previstos de recorrência e as parcelas nascem dentro da ação que os
  causou.
- **Alternativas**: middleware HTTP por rota (registraria tentativas que falharam e acopla
  tipos a URLs); eventos do SQLAlchemy (`after_insert`) (registrariam cada lançamento da
  importação e cada previsto gerado, violando FR-006).

## R2. Data e hora e ordem da linha do tempo

- **Decisão**: `ocorrido_em` com `server_default=now()`; ordem e paginação por `id` decrescente
  (keyset: `?antes=<id>`), 50 por página, devolvendo `proximo` (id) ou `null`.
- **Rationale**: o `id` é monotônico e único, então paginar por ele não repete nem pula itens,
  mesmo com eventos novos chegando no meio (cenário US2-4). Usar o horário do banco evita mudar
  a assinatura dos services que hoje não recebem `agora` (`excluir_lancamento`,
  `criar_categoria`, `desfazer_deposito`…).
- **Alternativas**: `offset/limit` (repete itens quando entram eventos novos); receber `agora`
  em todo service (é uma mudança grande, sem ganho).

## R3. Registro da abertura do detalhe sem burla e sem ruído

- **Decisão**: nova ação `ver_atividade` em `acao_admin`, registrada tanto no detalhe quanto na
  rota de eventos, no máximo uma vez a cada 30 minutos por administrador e conta (função pura
  `domain/atividade.precisa_registrar_visita`).
- **Rationale**: auditar só o detalhe deixaria a rota de eventos sem rastro. Auditar toda
  página encheria o histórico (US3) de linhas repetidas. Com a janela de 30 minutos, uma visita
  gera um registro, e nenhuma forma de ver a atividade escapa da auditoria.
- **Alternativas**: devolver a primeira página dentro do detalhe e auditar só ali (a rota de
  paginação continuaria sem auditoria).

## R4. Contagens por funcionalidade

- **Decisão**: uma consulta só, com subconsultas escalares, no padrão de
  `_uso_funcionalidades`. Lançamentos se dividem em:
  - `importados`: com `id_externo`;
  - `gerados`: com `recorrencia_id` ou `divida_id`, ou ligados a uma casa ou a um serviço;
  - `manuais`: o resto.
  Importações confirmadas = eventos `extrato_importado` (não há tabela de importação). Por
  isso começam do zero na entrada da feature, o que a spec já diz.
- **Rationale**: para o suporte, "digitou algo ou não" é o que importa, e lançamento gerado
  não indica uso.
- **Alternativas**: criar uma tabela de lote de importação (é dado novo só para contar);
  separar só manuais e importados (os gerados inflariam os manuais).

## R5. Sessões abertas e último acesso

- **Decisão**: sessões da conta com `ultimo_uso_em` dentro de `sessao_dias_inatividade`, o
  mesmo critério de `domain/login.sessao_expirada`. O último acesso é `usuario.ultimo_acesso_em`
  (feature 014), que tem precisão de dia.
- **Rationale**: o número bate com o que a autenticação aceitaria agora.

## R6. Retenção de 12 meses

- **Decisão**: novo comando `python -m app.cli limpar-eventos`, numa linha própria do
  `crontab` (06:00 UTC), que apaga os eventos anteriores a `domain/atividade.limite_retencao`
  (mesmo dia e hora, 12 meses antes; 29/02 vira 28/02).
- **Rationale**: o `enviar-lembretes` sai com erro quando o push está desligado. Pendurar a
  limpeza nele faria a retenção depender do push. O serviço de cron (supercronic) já existe;
  basta uma linha.
- **Alternativas**: limpar dentro do `enviar-lembretes` (acoplamento acima); limpar a cada
  gravação (custo em todo request).

## R7. Aviso de transparência

- **Decisão**: texto fixo no frontend, em `form-cadastro.tsx` (acima do botão) e em
  `form-perfil.tsx`: "O administrador vê quando você entra e quais recursos usa, mas nunca
  valores, descrições ou nomes do que você lança."
- **Rationale**: é informativo, sem aceite (premissa da spec), e a API não muda.

## R8. Rótulos dos tipos

- **Decisão**: a API devolve o código do tipo (`lancamento_criado`), e o frontend traduz por um
  mapa fixo.
- **Rationale**: o contrato fica estável e o texto mora na interface, como nas outras
  enumerações.
