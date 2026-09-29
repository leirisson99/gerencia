# Feature Specification: Limite por Categoria

**Feature Branch**: `009-limite-categoria`

**Created**: 2026-09-29

**Status**: Draft

**Input**: Pedido explícito do usuário (item P2 do Briefing, "Limite por categoria com aviso"):
"Cada categoria de saída pode ter um limite fixo que vale em todo ciclo. O resumo do ciclo mostra
quanto do limite foi usado e o sistema avisa quando um gasto aproxima ou estoura o limite."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Definir o limite de uma categoria (Priority: P1)

Defino quanto quero gastar, no máximo, em uma categoria de saída a cada ciclo (ex.: Lazer
R$ 300,00). Posso mudar ou remover o limite quando quiser.

**Why this priority**: sem limite definido não há o que acompanhar nem avisar.

**Independent Test**: definir um limite em "Lazer", consultar as categorias e ver o limite; remover
e ver que sumiu.

**Acceptance Scenarios**:

1. **Given** a categoria de saída "Lazer" sem limite, **When** defino o limite de R$ 300,00,
   **Then** a categoria passa a mostrar esse limite.
2. **Given** "Lazer" com limite, **When** mudo para R$ 400,00, **Then** o novo valor passa a valer
   em todos os ciclos, inclusive os passados.
3. **Given** "Lazer" com limite, **When** removo o limite, **Then** a categoria fica sem limite e
   deixa de ter acompanhamento.
4. **Given** a categoria de entrada "Renda extra", **When** tento definir um limite, **Then** o
   sistema recusa e explica que limite só vale para categorias de saída.
5. **Given** qualquer categoria de saída, **When** tento definir limite zero, negativo ou com
   fração de centavo, **Then** o sistema recusa.
6. **Given** uma nova categoria de saída, **When** a crio já informando o limite, **Then** ela nasce
   com esse limite.

---

### User Story 2 - Ver quanto do limite já usei no ciclo (Priority: P1)

No resumo do ciclo, cada categoria com limite mostra o total gasto, o limite e a situação: dentro
do limite, em atenção (80% ou mais) ou estourado (acima de 100%).

**Why this priority**: é o valor da feature: ver, antes do fim do ciclo, onde estou perto de
passar do planejado.

**Independent Test**: com limite de R$ 300,00 em Lazer, lançar gastos que somem R$ 100, R$ 250 e
R$ 320 e conferir a situação a cada passo.

**Acceptance Scenarios**:

1. **Given** Lazer com limite R$ 300,00 e R$ 100,00 gastos no ciclo, **When** peço o resumo,
   **Then** Lazer aparece com total R$ 100,00, limite R$ 300,00 e situação "ok".
2. **Given** R$ 240,00 gastos (exatamente 80%), **When** peço o resumo, **Then** a situação é
   "atenção".
3. **Given** R$ 300,00 gastos (exatamente 100%), **When** peço o resumo, **Then** a situação é
   "atenção", não "estourado".
4. **Given** R$ 300,01 gastos, **When** peço o resumo, **Then** a situação é "estourado".
5. **Given** Lazer com limite e nenhum gasto realizado no ciclo, **When** peço o resumo, **Then**
   Lazer aparece com total R$ 0,00 e situação "ok".
6. **Given** um gasto previsto de R$ 500,00 em Lazer (ex.: fixo ainda não pago), **When** peço o
   resumo, **Then** ele não conta no total nem muda a situação.
7. **Given** categorias sem limite, **When** peço o resumo, **Then** elas aparecem como antes, sem
   limite e sem situação.

---

### User Story 3 - Ser avisado ao lançar um gasto (Priority: P2)

Quando lanço ou corrijo um gasto e isso faz a categoria entrar em atenção ou estourar o limite, a
resposta do lançamento já traz o aviso, com quanto usei e qual é o limite.

**Why this priority**: o aviso na hora do gasto reforça o hábito; o resumo sozinho já entrega a
informação.

**Independent Test**: com limite de R$ 300,00 em Lazer e R$ 200,00 gastos, lançar R$ 50,00 e ver o
aviso de atenção; lançar mais R$ 10,00 e não ver aviso repetido; lançar R$ 50,00 e ver o aviso de
estourado.

**Acceptance Scenarios**:

1. **Given** Lazer com limite R$ 300,00 e R$ 200,00 gastos, **When** lanço R$ 50,00 em Lazer,
   **Then** o lançamento é aceito e a resposta traz aviso "atenção" com usado R$ 250,00 e limite
   R$ 300,00.
2. **Given** Lazer já em atenção (R$ 250,00), **When** lanço mais R$ 10,00, **Then** o lançamento é
   aceito sem aviso, pois a situação não piorou.
3. **Given** Lazer em atenção (R$ 260,00), **When** lanço R$ 50,00, **Then** a resposta traz aviso
   "estourado" com usado R$ 310,00.
4. **Given** Lazer com limite, **When** lanço um gasto previsto em Lazer, **Then** não há aviso.
5. **Given** um gasto previsto de R$ 100,00 em Lazer com R$ 220,00 já gastos, **When** confirmo o
   pagamento (previsto → realizado), **Then** a resposta traz aviso "atenção".
6. **Given** um gasto de R$ 50,00 em Alimentação, **When** mudo a categoria dele para Lazer e isso
   faz Lazer entrar em atenção, **Then** a resposta traz o aviso de Lazer.
7. **Given** Lazer em atenção no ciclo atual, **When** lanço um gasto em Lazer com data de um ciclo
   anterior que está bem abaixo do limite, **Then** não há aviso: a situação é a do ciclo da data
   do lançamento.
8. **Given** um lançamento que estoura o limite, **When** o lanço, **Then** ele é aceito
   normalmente: o limite nunca bloqueia um lançamento.

---

### Edge Cases

- Mudar o limite muda a situação de todos os ciclos, inclusive os fechados: o limite não tem
  histórico.
- Categoria desativada com limite: continua aparecendo no resumo se tiver gasto no ciclo; sem gasto,
  não aparece.
- Uma categoria que já tem limite não pode passar a ser de entrada: o tipo da categoria não muda
  (regra da feature 005).
- Lançamento que não conta no saldo (parcela paga no cartão) não conta no limite: o gasto já está
  na fatura.
- Excluir um gasto ou reduzir seu valor nunca gera aviso.
- Limite de R$ 0,01: qualquer gasto de R$ 0,02 ou mais estoura.
- Depósito na cartela é uma saída em "Poupança"; se o usuário der limite a "Poupança", os depósitos
  contam como qualquer gasto.
- Um usuário nunca vê nem altera o limite das categorias de outro.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Cada categoria de saída MUST poder ter um limite opcional, em centavos inteiros,
  maior que zero.
- **FR-002**: O sistema MUST recusar limite em categoria de entrada.
- **FR-003**: O usuário MUST poder definir o limite ao criar a categoria e definir, mudar ou
  remover o limite ao editá-la.
- **FR-004**: O limite MUST valer igualmente em todos os ciclos, sem histórico por ciclo.
- **FR-005**: O total usado de uma categoria num ciclo MUST seguir o mesmo filtro do saldo: só
  lançamentos realizados e que contam no saldo.
- **FR-006**: A situação MUST ser: "ok" quando o total usado é menor que 80% do limite; "atenção"
  de 80% até 100% inclusive; "estourado" acima de 100%. O cálculo MUST ser exato em centavos.
- **FR-007**: O resumo do ciclo MUST mostrar, para cada categoria de saída com limite, o limite e a
  situação, junto do total.
- **FR-008**: Categoria ativa com limite e sem gasto no ciclo MUST aparecer no resumo com total
  zero; isso substitui, só para essas categorias, a regra da feature 003 de não mostrar categoria
  sem lançamento.
- **FR-009**: As somas do resumo (saídas por categoria = total de saídas) MUST continuar fechando.
- **FR-010**: Ao criar ou editar um lançamento de saída realizado, a resposta MUST trazer um aviso
  quando a situação da categoria, no ciclo da data do lançamento, piora com a mudança (de "ok" para
  "atenção" ou "estourado", ou de "atenção" para "estourado"). O aviso informa a categoria, o total
  usado, o limite e a nova situação.
- **FR-011**: O limite MUST NOT bloquear nenhum lançamento.
- **FR-012**: Limites e avisos MUST considerar só dados do usuário autenticado.

### Key Entities

- **Limite da categoria**: valor em centavos, opcional, ligado a uma categoria de saída; vale em
  todos os ciclos.
- **Situação do limite** (derivada, não guardada): total usado no ciclo comparado ao limite: ok,
  atenção ou estourado.
- **Aviso de limite** (derivado, só na resposta do lançamento): categoria, total usado, limite e
  nova situação.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Definir um limite leva uma única ação e passa a valer na próxima consulta.
- **SC-002**: Em 100% dos casos de fronteira (79,99%, 80%, 100%, 100,01%), a situação bate com a
  regra conferida à mão.
- **SC-003**: Nenhum lançamento é recusado por causa de limite.
- **SC-004**: O aviso aparece uma vez por mudança de situação: lançar vários gastos seguidos na
  mesma situação não repete o aviso.
- **SC-005**: O resumo com limites continua respondendo em menos de 1 segundo.

## Assumptions

- Pedido explícito do usuário em 2026-09-29, item P2 do Briefing (Princípio VI).
- Depende das features 003 (resumo), 005 (categorias editáveis) e 001 (lançamentos).
- Limite é por categoria, não por ciclo; ajuste por ciclo específico fica fora.
- Previstos não contam no limite; a visão do que ainda vai sair fica na feature de projeção (010).
- O aviso é só informação na resposta; notificação por e-mail ou push fica fora.
- Não há limite para o total de saídas do ciclo, só por categoria.
- Escopo: backend e frontend (o frontend entrou em escopo em 2026-09-28): campo de limite nas
  categorias, medidor no resumo do dashboard e aviso ao lançar.
