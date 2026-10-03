# Feature Specification: Atividade do Usuário no Painel do Administrador

**Feature Branch**: `018-atividade-usuario`

**Created**: 2026-10-02

**Status**: Implementada (2026-10-03); falta validar no navegador (quickstart)

**Input**: "no painel do administrador ao clicar em cima de um usuario preciso visualizar o que
ele está fazendo dentro do sistema". Decisão do usuário: opção B, ou seja, o uso da conta sem
o conteúdo (sem valores, descrições, categorias ou nomes). Objetivo: suporte (ver quem está
travado) e engajamento (ver quem parou de usar). Constituição 6.0.0, princípio V.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ver o resumo de uso de uma conta (Priority: P1)

Na lista de contas, o administrador clica numa conta e abre o detalhe dela, que mostra: nome,
e-mail, data de criação, situação, último acesso, quantas sessões estão abertas e quantos
registros a conta tem em cada funcionalidade. Com isso ele vê, em segundos, se a pessoa entrou,
o que já usou e o que nunca tocou.

**Why this priority**: responde sozinha às duas perguntas do objetivo ("está usando?" e "usa o
quê?") e funciona com os dados que já existem, sem esperar eventos novos se acumularem.

**Independent Test**: com a Ana tendo 5 lançamentos manuais, 3 importados, 1 cartela com 2
depósitos e nenhum serviço, abrir o detalhe dela e conferir cada número. Nenhum valor em reais
ou texto digitado por ela pode aparecer.

**Acceptance Scenarios**:

1. **Given** a Ana com lançamentos manuais e importados, recorrências, dívidas, cartelas com
   depósitos, serviços, lembretes livres e aparelhos com push, **When** o administrador abre o
   detalhe dela, **Then** vê a quantidade de cada um, com zero no que ela nunca usou.
2. **Given** a Ana logada em dois aparelhos, **Then** o detalhe mostra 2 sessões abertas.
3. **Given** a Ana com último acesso registrado, **Then** o detalhe mostra a data desse
   acesso; se ela nunca entrou depois que o registro começou, mostra "nunca".
4. **Given** qualquer conta, **Then** nada no detalhe traz valores em reais, saldos,
   descrições, nomes de categorias, de pessoas, de clientes ou de cartelas, textos de
   lembretes, telefone, cargo ou data de nascimento.
5. **Given** uma conta inexistente ou a do próprio administrador, **Then** a resposta é 404.
6. **Given** um usuário comum, **When** tenta abrir o detalhe de qualquer conta, inclusive a
   própria, **Then** o acesso é negado, como nas demais rotas do administrador.
7. **Given** o administrador abre o detalhe da Ana, **Then** essa abertura fica registrada
   nas ações administrativas (quem, em quem, quando).

---

### User Story 2 - Linha do tempo de uso (Priority: P1)

O detalhe da conta traz uma linha do tempo com o que a pessoa fez, do mais recente para o mais
antigo. Cada item tem só o tipo da ação e a data e hora, por exemplo "entrou no sistema",
"lançou", "editou lançamento", "importou extrato" ou "depositou em cartela". A lista é
paginada.

**Why this priority**: é o que mostra onde a pessoa travou (por exemplo, entrou três vezes e
nunca lançou nada) e quando parou de usar.

**Independent Test**: logar como a Ana, criar um lançamento, editá-lo, importar um extrato e
depositar numa cartela. O detalhe dela deve mostrar esses cinco eventos, na ordem inversa,
sem nenhum conteúdo das ações.

**Acceptance Scenarios**:

1. **Given** a Ana faz login, **Then** surge o evento "entrou no sistema" com data e hora.
2. **Given** a Ana cria, edita e exclui um lançamento, **Then** surgem três eventos dos tipos
   correspondentes, do mais recente para o mais antigo.
3. **Given** a Ana confirma uma importação com 20 linhas, **Then** surge um único evento
   "importou extrato", e não 20 eventos de lançamento.
4. **Given** mais eventos do que cabem numa página, **When** o administrador pede a próxima,
   **Then** recebe os seguintes, sem repetir nem pular nenhum.
5. **Given** uma ação que falha (por exemplo, um lançamento recusado por estar antes do
   primeiro salário), **Then** nenhum evento é registrado.
6. **Given** a Ana e o Bruno usando o sistema, **Then** a linha do tempo da Ana só traz os
   eventos dela.
7. **Given** um lançamento previsto gerado automaticamente (recorrência ao abrir o ciclo,
   parcelas de uma dívida), **Then** não vira evento separado; só a ação da pessoa que o
   causou (por exemplo, "lançou salário" ou "criou dívida") aparece.

---

### User Story 3 - Histórico das ações do administrador sobre a conta (Priority: P2)

O detalhe mostra também as ações administrativas feitas sobre a conta: resets de senha,
desativações, reativações e aberturas do detalhe, com quem fez e quando.

**Why this priority**: ajuda o suporte ("já resetei a senha dela ontem?"), mas não é o centro
do pedido.

**Independent Test**: resetar a senha da Ana, desativar, reativar e abrir o detalhe; as quatro
ações aparecem, da mais recente para a mais antiga.

**Acceptance Scenarios**:

1. **Given** resets, desativações e reativações da Ana, **Then** o detalhe lista cada ação
   com o tipo, a data e hora e o administrador que a fez.
2. **Given** ações sobre o Bruno, **Then** elas não aparecem no detalhe da Ana.

---

### User Story 4 - Aviso de transparência ao usuário (Priority: P1)

Quem se cadastra fica sabendo, no cadastro e no perfil, que o administrador vê o uso da conta
(quando entrou, o que usou e quantos registros tem), mas nunca valores nem o conteúdo do que
foi lançado.

**Why this priority**: é exigido pela constituição 6.0.0 e precisa estar no ar quando o detalhe
for liberado.

**Independent Test**: abrir a tela de cadastro e o perfil e encontrar o aviso nos dois.

**Acceptance Scenarios**:

1. **Given** a tela de cadastro, **Then** o aviso aparece antes do botão de criar conta.
2. **Given** a página de perfil, **Then** o mesmo aviso aparece.

---

### Edge Cases

- Conta criada antes desta feature: a linha do tempo começa vazia e mostra "sem atividade
  registrada desde" seguido da data em que a feature entrou no ar; as contagens por funcionalidade já vêm completas, porque
  vêm dos registros que existem.
- Conta desativada: o detalhe abre normalmente, e as sessões aparecem como 0.
- Conta com milhares de eventos: a paginação mantém o detalhe rápido.
- Eventos do próprio administrador não são registrados, porque ele não usa as funções
  financeiras.
- Login recusado (senha errada ou conta desativada) não vira evento de uso; o bloqueio de login
  já tem o próprio registro.
- Uso de sessão (cada requisição) não vira evento; só o login vira "entrou no sistema".
- Ao apagar uma conta (quando existir), os eventos dela vão junto.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O administrador MUST poder abrir o detalhe de qualquer conta de usuário comum.
  Conta inexistente ou do próprio administrador MUST retornar 404, e usuário comum MUST ter o
  acesso negado.
- **FR-002**: O detalhe MUST trazer nome, e-mail, data de criação, situação, último acesso
  (ou "nunca") e quantidade de sessões abertas.
- **FR-003**: O detalhe MUST trazer a quantidade de registros da conta em cada funcionalidade:
  lançamentos manuais (digitados pela pessoa), lançamentos importados, lançamentos gerados
  pelo sistema (recorrências, parcelas, depósitos em cartela, serviços), importações
  confirmadas (contadas pelos eventos, desde a entrada da feature), recorrências,
  dívidas, cartelas, depósitos em cartela, serviços, lembretes livres e aparelhos com push.
  Funcionalidade não usada MUST aparecer com zero.
- **FR-004**: O sistema MUST registrar um evento de uso a cada ação bem-sucedida da pessoa,
  guardando só a conta, o tipo da ação e a data e hora. Os tipos são uma lista fechada:
  criou a conta; entrou no sistema; lançou, editou e excluiu lançamento; importou extrato; criou e editou
  recorrência; criou dívida; criou cartela, depositou e desfez depósito; criou, editou e
  excluiu serviço, marcou e desfez recebimento; criou, editou, concluiu e excluiu lembrete;
  criou e editou categoria; atualizou o perfil; trocou a senha; ativou e removeu push.
- **FR-005**: Eventos de uso MUST NOT guardar valores, descrições, nomes de categorias, de
  pessoas, de clientes ou de cartelas, textos, nem o identificador do registro afetado.
- **FR-006**: Uma ação que falha MUST NOT gerar evento. Uma importação confirmada MUST gerar um
  único evento. Lançamentos gerados automaticamente (recorrências, parcelas) MUST NOT gerar
  eventos próprios.
- **FR-007**: O detalhe MUST trazer a linha do tempo de eventos da conta, do mais recente para
  o mais antigo, paginada, com páginas de até 50 itens.
- **FR-008**: O detalhe MUST trazer as ações administrativas sobre a conta, com tipo, data e
  hora e quem fez.
- **FR-009**: Abrir o detalhe MUST ser registrado como ação administrativa. Pedir outras
  páginas da linha do tempo na mesma visita MUST NOT gerar novos registros: uma visita do
  mesmo administrador à mesma conta vale por 30 minutos.
- **FR-010**: Nenhuma resposta do detalhe MUST trazer valores em reais, saldos, descrições,
  nomes de categorias, de pessoas, de clientes ou de cartelas, textos de lembretes, telefone,
  cargo ou data de nascimento.
- **FR-011**: As telas de cadastro e de perfil MUST avisar que o administrador vê o uso da
  conta, sem valores nem conteúdo.
- **FR-012**: Eventos de uso MUST ser guardados por 12 meses e apagados depois disso pela
  rotina diária que já existe.
- **FR-013**: Na lista de contas do painel, clicar numa conta MUST abrir o detalhe dela.

### Key Entities

- **Evento de uso**: uma ação bem-sucedida de uma conta. Tem só a conta, o tipo da ação (de uma
  lista fechada) e a data e hora. Não aponta para o registro afetado nem guarda o conteúdo.
- **Ação administrativa** (já existe): passa a ter também o tipo "abriu o detalhe da conta".
- **Detalhe da conta** (derivado, não armazenado): junta os dados cadastrais permitidos, o
  último acesso, as sessões abertas, as contagens por funcionalidade, a linha do tempo e as
  ações administrativas.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: O administrador descobre se uma conta está ativa e qual funcionalidade ela nunca
  usou em menos de 10 segundos depois de clicar na conta.
- **SC-002**: Em uma varredura de todas as respostas do detalhe nos testes, nenhuma contém
  valor monetário, descrição, nome de categoria, de pessoa, de cliente ou de cartela, nem texto
  digitado pelo usuário.
- **SC-003**: 100% das ações bem-sucedidas listadas em FR-004 geram exatamente um evento, e 0%
  das ações que falham geram evento.
- **SC-004**: 100% das aberturas de detalhe ficam registradas nas ações administrativas.
- **SC-005**: O detalhe de uma conta com 10 mil eventos abre tão rápido quanto o de uma conta
  nova, sem espera perceptível.

## Assumptions

- O último acesso é o que já é guardado desde a feature 014: tem precisão de dia e é atualizado
  no máximo uma vez por dia. A hora exata do login aparece na linha do tempo ("entrou no
  sistema").
- "Sessões abertas" = sessões da conta que ainda valem, pelo mesmo critério que a autenticação
  usa.
- Retenção de 12 meses: tempo suficiente para ver quem parou de usar e limitado para não virar
  um histórico permanente do comportamento de cada pessoa. A limpeza entra no comando diário
  que já roda (o mesmo do resumo de lembretes).
- O detalhe abre numa página própria do painel, em largura total, como
  as outras páginas de dados.
- O aviso de transparência é um texto curto e fixo. Não há aceite nem opção de recusar: o
  administrador ver o uso sem conteúdo é condição de uso do sistema.
- O administrador não ganha filtros nem busca na linha do tempo nesta versão, só a paginação.
- Escopo backend e frontend.
