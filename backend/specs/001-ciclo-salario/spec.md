# Feature Specification: Ciclo Aberto pelo Salário

**Feature Branch**: `001-ciclo-salario`

**Created**: 2026-09-28

**Status**: Draft

**Input**: User description: "vamos usar postgres esse sistema vai rodar na web" — refinado na
conversa: o ciclo começa quando o usuário lança o salário manualmente; não há cálculo de dia de
pagamento.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Lançar o salário e abrir um ciclo (Priority: P1)

Quando o salário cai na conta, eu lanço uma entrada na categoria "Salário" com valor e data.
Esse lançamento abre um novo ciclo, que dura até a véspera do próximo salário que eu lançar.

**Why this priority**: sem ciclo aberto nada mais pode ser lançado; é a porta de entrada do
sistema.

**Independent Test**: lançar um salário e ver um ciclo aberto começando na data dele, sem data
de fim; lançar um segundo salário e ver o primeiro ciclo fechado na véspera.

**Acceptance Scenarios**:

1. **Given** nenhum salário lançado, **When** lanço R$ 5.000,00 em "Salário" com data
   05/10/2026, **Then** existe um ciclo aberto que começa em 05/10/2026 e não tem data de fim.
2. **Given** o ciclo aberto desde 05/10/2026, **When** lanço um salário com data 06/11/2026,
   **Then** o ciclo anterior passa a ser 05/10/2026 a 05/11/2026 e um novo ciclo aberto começa
   em 06/11/2026.
3. **Given** um ciclo aberto, **When** lanço uma entrada em "Renda extra" (ex.: 13º), **Then**
   nenhum ciclo novo é aberto e a entrada conta no ciclo em que sua data cai.
4. **Given** qualquer estado, **When** tento lançar um salário com data futura, **Then** o
   sistema recusa e explica que o salário é lançado quando entra.

---

### User Story 2 - Bloqueio antes do primeiro salário (Priority: P1)

Enquanto eu não tiver lançado nenhum salário, o sistema não aceita outros lançamentos e me
orienta a lançar o salário primeiro.

**Why this priority**: garante que todo lançamento pertença a um ciclo; sem isso o saldo e o
gasto por categoria ficam sem moldura.

**Independent Test**: com um usuário novo, tentar lançar um gasto e ver a recusa com a
orientação; lançar o salário e então conseguir lançar o gasto.

**Acceptance Scenarios**:

1. **Given** usuário sem salário lançado, **When** tento lançar um gasto, **Then** o sistema
   recusa com a mensagem "lance seu salário para abrir o primeiro ciclo".
2. **Given** primeiro salário lançado em 05/10/2026, **When** tento lançar um gasto com data
   01/10/2026, **Then** o sistema recusa, pois a data é anterior ao primeiro ciclo.
3. **Given** primeiro salário lançado em 05/10/2026, **When** lanço um gasto com data
   05/10/2026, **Then** o gasto é aceito e pertence ao ciclo que começa nesse dia.

---

### User Story 3 - Ver o ciclo atual e navegar entre ciclos (Priority: P2)

Vejo o ciclo em que estou (o mais recente) e posso ir para o anterior ou o próximo.

**Why this priority**: permite rever ciclos passados; o ciclo atual já entrega valor sozinho.

**Independent Test**: com três salários lançados, navegar do atual até o primeiro e voltar,
conferindo que não há buraco nem sobreposição de dias.

**Acceptance Scenarios**:

1. **Given** salários em 05/10, 06/11 e 05/12/2026, **When** abro o sistema em 10/12/2026,
   **Then** vejo o ciclo aberto que começa em 05/12/2026.
2. **Given** o ciclo 06/11/2026 a 04/12/2026, **When** peço o anterior, **Then** recebo
   05/10/2026 a 05/11/2026; **When** peço o próximo, **Then** recebo o ciclo aberto desde
   05/12/2026.
3. **Given** o primeiro ciclo, **When** peço o anterior, **Then** o sistema informa que não
   existe ciclo anterior; o mesmo vale para o próximo do ciclo aberto.
4. **Given** qualquer data a partir do primeiro salário, **When** pergunto a qual ciclo ela
   pertence, **Then** recebo exatamente um ciclo.

---

### User Story 4 - Corrigir ou excluir um salário (Priority: P2)

Se eu errar a data de um salário ou excluí-lo, os ciclos se reorganizam sozinhos.

**Why this priority**: erros de digitação acontecem; o ciclo derivado precisa acompanhar a
correção sem trabalho manual.

**Independent Test**: mudar a data de um salário do meio e conferir que os ciclos vizinhos
mudam de limite; excluir um salário e ver dois ciclos virarem um.

**Acceptance Scenarios**:

1. **Given** salários em 05/10 e 06/11/2026, **When** mudo o segundo para 04/11/2026, **Then**
   os ciclos passam a ser 05/10 a 03/11/2026 e o aberto desde 04/11/2026, e os lançamentos
   passam a pertencer ao ciclo em que sua data cai.
2. **Given** salários em 05/10, 06/11 e 05/12/2026, **When** excluo o de 06/11, **Then** existe
   um ciclo de 05/10 a 04/12/2026.
3. **Given** um único salário e outros lançamentos, **When** tento excluí-lo ou movê-lo para
   depois de algum lançamento, **Then** o sistema recusa, pois lançamentos ficariam sem ciclo.

---

### Edge Cases

- Dois salários na mesma data pertencem ao mesmo ciclo; não existe ciclo de zero dias.
- Ciclos têm qualquer duração (ex.: 20 ou 40 dias); não há validação de tamanho.
- Virada de ano: um ciclo aberto em 20/12/2026 segue até a véspera do próximo salário em 2027.
- Mudar a categoria de um lançamento para ou de "Salário" tem o mesmo efeito de criar ou
  excluir um salário, com as mesmas recusas.
- Qualquer alteração que deixaria algum lançamento com data anterior ao primeiro salário é
  recusada.
- Um usuário nunca vê nem afeta os ciclos de outro usuário.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Cada usuário MUST ter a categoria de entrada "Salário" criada automaticamente, que
  não pode ser excluída nem renomeada, e que é a única categoria que abre ciclo.
- **FR-002**: Um lançamento de entrada, realizado, na categoria "Salário" MUST abrir um ciclo
  na sua data.
- **FR-003**: Um ciclo MUST ir da data de um salário até a véspera da próxima data de salário
  distinta; o ciclo do salário mais recente MUST ficar aberto, sem data de fim.
- **FR-004**: O sistema MUST recusar salário com data posterior a hoje (fuso de São Paulo).
- **FR-005**: Enquanto o usuário não tiver salário lançado, o sistema MUST recusar qualquer
  outro lançamento, com orientação para lançar o salário.
- **FR-006**: O sistema MUST recusar lançamentos com data anterior ao primeiro salário, e
  qualquer alteração ou exclusão de salário que deixe lançamentos nessa situação.
- **FR-007**: Todo lançamento MUST pertencer ao ciclo em que sua data cai.
- **FR-008**: O sistema MUST mostrar o ciclo atual (o mais recente) e permitir navegar para o
  anterior e o próximo, informando quando não houver.
- **FR-009**: O sistema MUST informar a qual ciclo pertence qualquer data a partir do primeiro
  salário.
- **FR-010**: Ciclos MUST ser derivados das datas dos salários do usuário, nunca guardados;
  qualquer mudança de data, categoria ou exclusão de salário MUST refletir na próxima consulta.
- **FR-011**: Ao abrir um ciclo, o sistema MUST disparar a geração dos gastos fixos previstos
  daquele ciclo (regra detalhada na feature de recorrências).
- **FR-012**: Ao lançar um salário, o sistema SHOULD sugerir o valor do último salário lançado.
- **FR-013**: Ciclos e lançamentos MUST ser visíveis e alteráveis só pelo próprio usuário.

### Key Entities

- **Lançamento de salário**: lançamento comum (valor, categoria "Salário", data, descrição
  opcional) cuja data marca o início de um ciclo.
- **Categoria "Salário"**: categoria de entrada do sistema, uma por usuário, protegida.
- **Ciclo** (derivado, não guardado): data de início e data de fim (vazia no ciclo aberto),
  obtidos das datas dos salários do usuário.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Lançar o salário e consultar o ciclo aberto respondem, cada um, em menos de 1
  segundo.
- **SC-002**: Para qualquer sequência de salários, toda data a partir do primeiro pertence a
  exatamente um ciclo (sem buracos nem sobreposições).
- **SC-003**: 100% dos exemplos de aceitação desta spec batem com o calendário conferido à mão.
- **SC-004**: Após corrigir ou excluir um salário, os ciclos exibidos refletem a mudança na
  próxima consulta, sem ação extra do usuário.
- **SC-005**: Nenhum lançamento aceito fica fora de um ciclo.

## Assumptions

- Depende da feature de cadastro e login (002): todo ciclo é de um usuário autenticado.
- Não existe configuração de pagamento: sem salário configurado, dia fixo, dia útil ou
  feriados. A tabela de configuração deixa de existir.
- O salário é sempre lançado manualmente e não é uma recorrência.
- 13º, adiantamentos e outras entradas vão para outras categorias de entrada (ex.: "Renda
  extra"), que não abrem ciclo.
- A regra de geração de gastos fixos por ciclo (um previsto por recorrência, na próxima
  ocorrência do dia a partir do início do ciclo; pendentes ficam no ciclo antigo) será
  especificada na feature de recorrências.
- Saldo e gasto por categoria do ciclo ficam na feature da tela do ciclo.
- O sistema roda na web com banco PostgreSQL.
