# Feature Specification: Lembretes por Push

**Feature Branch**: `015-lembretes-push`

**Created**: 2026-10-01

**Status**: Implementada (2026-10-01)

**Input**: Pedido explícito do usuário em 2026-10-01: ser avisado no celular do que vence, sem
precisar abrir o app. Decisões do usuário: notificação push pelo app instalado (PWA); avisar
contas a pagar, valores a receber e lembretes livres; janela fixa de 3 dias; resumo diário às 8h;
sem valores nem nomes na notificação. Constituição 5.1.0 (Princípio VI, "Lembretes").

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ver o que vence nos próximos dias (Priority: P1)

Abro a página de lembretes e vejo, separado em "atrasados" e "a vencer", o que tenho a pagar e a
receber até daqui a 3 dias, com valor, data e descrição, além dos meus lembretes livres.

**Why this priority**: é o destino de toda notificação e já resolve o problema para quem abre o
app; sem a página, o push não teria onde mostrar os detalhes.

**Independent Test**: com o aluguel previsto para daqui a 2 dias, a internet prevista para ontem
e um serviço a receber daqui a 5 dias, abrir os lembretes e ver a internet em "atrasados", o
aluguel em "a vencer" e o serviço fora da lista.

**Acceptance Scenarios**:

1. **Given** hoje é 10/10 e tenho uma saída prevista de R$ 1.500,00 em 12/10, **When** abro os
   lembretes, **Then** ela aparece em "a vencer", como conta a pagar, com valor, data, categoria e
   descrição.
2. **Given** uma saída prevista em 13/10 (hoje + 3), **When** abro os lembretes, **Then** ela
   aparece; uma em 14/10 (hoje + 4) não aparece.
3. **Given** uma saída prevista em 08/10 que nunca confirmei, **When** abro os lembretes, **Then**
   ela aparece em "atrasados", por mais antiga que seja.
4. **Given** uma entrada prevista em 11/10 (serviço, parcela que me devem ou recorrência de
   entrada), **When** abro os lembretes, **Then** ela aparece como valor a receber.
5. **Given** uma parcela prevista paga no cartão (que não conta no saldo), **When** abro os
   lembretes, **Then** ela não aparece: quem é pago é a fatura.
6. **Given** confirmei a saída de 12/10 como realizada, **When** abro os lembretes, **Then** ela
   não aparece mais.
7. **Given** outra pessoa com contas vencendo, **When** abro os meus lembretes, **Then** não vejo
   as dela.

---

### User Story 2 - Receber o resumo diário no celular (Priority: P1)

Ativo as notificações no meu celular. Toda manhã, por volta das 8h, se houver algo atrasado ou
vencendo, recebo uma notificação com um resumo em números, sem valores. Ao tocar, abro a página
de lembretes.

**Why this priority**: é o pedido central: ser lembrado sem precisar lembrar de abrir o app.

**Independent Test**: ativar as notificações, ter duas contas vencendo e um valor atrasado, rodar
o envio do dia e receber uma notificação com essas contagens; rodar de novo e não receber outra.

**Acceptance Scenarios**:

1. **Given** ativei as notificações neste aparelho e tenho 2 contas a vencer e 1 valor a receber
   atrasado, **When** o envio do dia roda, **Then** recebo uma notificação com essas contagens e
   sem valores em reais, descrições, categorias ou nomes.
2. **Given** recebi o resumo de hoje, **When** o envio roda de novo no mesmo dia, **Then** não
   recebo outra notificação.
3. **Given** não tenho nada atrasado, a vencer nem lembrete livre na janela, **When** o envio
   roda, **Then** não recebo notificação.
4. **Given** ativei em dois aparelhos, **When** o envio roda, **Then** os dois recebem o mesmo
   resumo.
5. **Given** toco na notificação, **When** o app abre, **Then** vejo a página de lembretes (ou o
   login, se a sessão tiver expirado, e depois a página).
6. **Given** um aparelho cuja autorização foi revogada ou expirou, **When** o envio tenta
   notificá-lo, **Then** esse aparelho é removido da minha lista e os outros recebem normalmente.

---

### User Story 3 - Ativar e desativar as notificações (Priority: P1)

No perfil, ativo as notificações neste aparelho. Depois posso desativá-las. Se o aparelho não
suporta notificações (ou é um iPhone sem o app instalado), vejo uma explicação de como fazer.

**Why this priority**: sem a autorização do aparelho não existe push.

**Independent Test**: ativar no perfil, ver o aparelho como ativo; desativar e não receber mais o
resumo nele.

**Acceptance Scenarios**:

1. **Given** estou no perfil num aparelho compatível, **When** ativo as notificações e autorizo,
   **Then** o aparelho passa a receber o resumo e o perfil mostra "ativadas neste aparelho".
2. **Given** nego a autorização no aviso do aparelho, **When** volto ao perfil, **Then** vejo que
   as notificações estão bloqueadas e como liberar nas configurações.
3. **Given** as notificações estão ativas neste aparelho, **When** as desativo, **Then** este
   aparelho deixa de receber o resumo e os outros continuam.
4. **Given** estou num iPhone pelo navegador, sem o app instalado, **When** abro o perfil,
   **Then** vejo que preciso adicionar o app à tela inicial para ativar as notificações.
5. **Given** saio da conta neste aparelho, **When** o envio roda, **Then** este aparelho não
   recebe o meu resumo.
6. **Given** outra pessoa entra na conta dela no mesmo aparelho e ativa as notificações,
   **When** o envio roda, **Then** o aparelho recebe só o resumo dela.

---

### User Story 4 - Criar lembretes livres (Priority: P2)

Crio um lembrete com um texto e uma data, como "renovar o seguro do carro" em 15/10. Ele entra
nos lembretes e no resumo quando estiver a até 3 dias. Quando resolvo, marco como concluído ou
excluo.

**Why this priority**: cobre o que não é lançamento; contas e valores já entregam a maior parte
do valor.

**Independent Test**: criar "renovar seguro" para daqui a 2 dias, vê-lo em "a vencer" e no
resumo, concluir e vê-lo sair.

**Acceptance Scenarios**:

1. **Given** hoje é 10/10, **When** crio "renovar seguro" para 12/10, **Then** ele aparece em "a
   vencer" e conta no resumo do dia.
2. **Given** um lembrete livre para 20/10, **When** abro os lembretes, **Then** ele aparece na
   lista de lembretes livres futuros, mas não em "a vencer" nem no resumo.
3. **Given** um lembrete livre de 08/10 não concluído, **When** abro os lembretes, **Then** ele
   aparece em "atrasados".
4. **Given** um lembrete pendente, **When** o marco como concluído, **Then** ele sai dos atrasados
   e do resumo e fica visível como concluído; posso desfazer a conclusão.
5. **Given** um lembrete, **When** edito o texto ou a data, ou o excluo, **Then** a mudança vale
   na hora para a página e para o próximo resumo.
6. **Given** um texto vazio, só com espaços ou com mais de 200 caracteres, ou sem data, **When**
   tento salvar, **Then** o lembrete é recusado e o campo é apontado.
7. **Given** um lembrete de outra pessoa, **When** tento abrir, editar, concluir ou excluir,
   **Then** ele não é encontrado.

---

### Edge Cases

- A janela é contada em dias no fuso de São Paulo: "a vencer" vai de hoje até hoje + 3,
  inclusive; "atrasado" é qualquer data anterior a hoje. Uma conta com data de hoje está "a
  vencer", não atrasada.
- Previstos de ciclos anteriores que nunca foram confirmados continuam como atrasados; a janela
  não depende do ciclo nem do tipo de renda.
- Depósitos de cartela não aparecem: já nascem realizados e não contam no saldo.
- O "Salário" previsto de um prestador aparece como valor a receber, como qualquer entrada
  prevista.
- Conta desativada pelo administrador não recebe resumo, mesmo com aparelhos ativos.
- O administrador não tem lembretes (não tem dados financeiros).
- Se nenhum aparelho do usuário recebe o resumo por falha temporária, o envio do dia continua
  pendente e é tentado de novo numa próxima execução do mesmo dia.
- O texto da notificação nunca leva valores, descrições, categorias, nomes de clientes ou de
  pessoas, nem o texto dos lembretes livres: só contagens.
- Mudanças feitas depois do envio (confirmar uma conta, concluir um lembrete) não geram nova
  notificação no mesmo dia.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST listar, para o usuário autenticado, as contas a pagar: saídas
  previstas que contam no saldo, com data até hoje + 3 dias, incluindo as atrasadas.
- **FR-002**: O sistema MUST listar os valores a receber: entradas previstas com data até hoje +
  3 dias, incluindo as atrasadas.
- **FR-003**: Contas a pagar e valores a receber MUST ser derivados dos lançamentos previstos no
  momento da consulta, nunca guardados; confirmar, editar ou excluir o lançamento muda a lista na
  hora.
- **FR-004**: Cada item MUST indicar se está atrasado ou a vencer e trazer o valor, a data, a
  categoria e a descrição do lançamento.
- **FR-005**: Usuários MUST poder criar, editar, concluir, desfazer a conclusão e excluir
  lembretes livres com texto (obrigatório, até 200 caracteres) e data (obrigatória, passada ou
  futura).
- **FR-006**: Lembretes livres não concluídos com data até hoje + 3 dias MUST entrar em
  "atrasados" ou "a vencer" e no resumo; os demais MUST aparecer na lista de lembretes livres
  sem entrar no resumo.
- **FR-007**: Usuários MUST poder ativar as notificações num aparelho e desativá-las nesse
  aparelho, podendo ter vários aparelhos ativos ao mesmo tempo.
- **FR-008**: Um aparelho MUST receber o resumo de um único usuário: ativá-lo para outro usuário
  o transfere; sair da conta no aparelho MUST desativá-lo.
- **FR-009**: Uma vez por dia, por volta das 8h no fuso de São Paulo, o sistema MUST enviar a
  cada usuário ativo com pelo menos um item atrasado ou a vencer um resumo para todos os seus
  aparelhos ativos.
- **FR-010**: O resumo MUST conter só contagens (contas a pagar, valores a receber e lembretes,
  separando atrasados) e texto genérico; MUST NOT conter valores em reais, descrições,
  categorias, nomes de pessoas ou clientes, nem o texto de lembretes livres.
- **FR-011**: O sistema MUST enviar no máximo um resumo por usuário por dia, mesmo que o envio
  rode mais de uma vez; o dia só conta como enviado quando ao menos um aparelho recebe.
- **FR-012**: Usuários sem nada atrasado ou a vencer, contas desativadas e o administrador MUST
  NOT receber resumo.
- **FR-013**: Aparelhos cuja autorização foi revogada ou expirou MUST ser removidos quando o
  envio detectar a recusa, sem afetar os outros aparelhos.
- **FR-014**: Tocar na notificação MUST abrir a página de lembretes do app.
- **FR-015**: O envio MUST ser disparado por uma tarefa agendada, nunca durante uma requisição
  do usuário.
- **FR-016**: Lembretes livres e aparelhos MUST ser visíveis e alteráveis só pelo próprio
  usuário; os de outro MUST ser tratados como não encontrados.
- **FR-017**: O perfil MUST mostrar se as notificações estão ativas, bloqueadas ou indisponíveis
  neste aparelho, e explicar como resolver quando bloqueadas ou indisponíveis (incluindo o caso
  do iPhone sem o app instalado).
- **FR-018**: Registros de execução do envio MUST NOT conter dados pessoais, valores, descrições
  ou endereços de aparelhos; só contagens.

### Key Entities

- **Lembrete** (derivado): conta a pagar ou valor a receber vindo de um lançamento previsto, com
  a situação "atrasado" ou "a vencer".
- **Lembrete livre**: texto, data e, quando concluído, a data da conclusão; pertence a um usuário.
- **Aparelho inscrito**: autorização de um aparelho para receber notificações de um usuário.
- **Envio do dia**: marca de que o resumo de um dia já chegou a um usuário.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em 100% dos casos de fronteira (ontem, hoje, hoje + 3 e hoje + 4), um lançamento
  previsto aparece ou não nos lembretes conforme a regra da janela.
- **SC-002**: Nenhum usuário recebe mais de uma notificação de resumo por dia, mesmo com o envio
  rodando várias vezes.
- **SC-003**: Nenhuma notificação contém valor em reais, descrição, categoria ou nome; verificável
  em 100% das mensagens geradas nos testes.
- **SC-004**: Quem tem algo vencendo e um aparelho ativo recebe o resumo até as 8h30 do dia.
- **SC-005**: Ativar as notificações leva no máximo dois toques a partir do perfil (botão e
  autorização do aparelho).
- **SC-006**: Nenhum usuário vê, altera ou recebe lembretes de outro.

## Assumptions

- Pedido explícito do usuário em 2026-10-01; constituição 5.1.0. O Briefing pedia 2 ciclos de
  uso antes de itens P1; o usuário decidiu seguir.
- Escopo: backend (API e tarefa de envio) e frontend (página de lembretes, ativação no perfil e
  recebimento das notificações no app instalado).
- Canal: notificação push do app instalado (PWA), com chaves do servidor em variáveis de
  ambiente. A tarefa de envio é um comando do próprio sistema, agendado no servidor (cron)
  para as 8h de São Paulo.
- iPhone recebe notificações só com o app adicionado à tela inicial (iOS 16.4 ou mais novo);
  Android e computadores recebem pelo navegador.
- A janela é fixa em 3 dias; não há configuração por usuário.
- Lembretes livres não têm hora nem repetição; a "data" é só o dia.
- Fora do escopo: e-mail, antecedência configurável, lembrete com hora, lembrete livre
  recorrente, aviso de limite de categoria por push, notificação a cada lançamento ou mudança.
