# Feature Specification: Resumo do Ciclo

**Feature Branch**: `003-resumo-ciclo`

**Created**: 2026-09-28

**Status**: Draft

**Input**: Próximo passo da lista: "Resumo do ciclo: saldo e gasto por categoria — o objetivo
central do produto (quanto entrou, para onde foi, quanto sobrou)."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ver quanto entrou, saiu e sobrou no ciclo (Priority: P1)

Para qualquer ciclo, vejo o total de entradas, o total de saídas e o saldo (entradas − saídas),
contando só o que de fato aconteceu.

**Why this priority**: é a pergunta central do produto: quanto sobrou do salário.

**Independent Test**: com salário, uma renda extra e alguns gastos lançados num ciclo, pedir o
resumo e conferir os três totais.

**Acceptance Scenarios**:

1. **Given** um ciclo com salário de R$ 5.000,00, renda extra de R$ 300,00 e gastos de R$ 800,00
   (Alimentação) e R$ 1.500,00 (Moradia), **When** peço o resumo, **Then** vejo entradas
   R$ 5.300,00, saídas R$ 2.300,00 e saldo R$ 3.000,00.
2. **Given** o mesmo ciclo com um gasto **previsto** de R$ 100,00, **When** peço o resumo,
   **Then** os totais não mudam.
3. **Given** um lançamento que não conta no saldo (ex.: parcela paga no cartão), **When** peço o
   resumo, **Then** ele não entra em nenhum total.
4. **Given** saídas maiores que as entradas, **When** peço o resumo, **Then** o saldo é negativo.
5. **Given** lançamentos de outros ciclos, **When** peço o resumo de um ciclo, **Then** só os
   lançamentos com data dentro dele contam.

---

### User Story 2 - Ver para onde o dinheiro foi, por categoria (Priority: P1)

No mesmo resumo, vejo o total gasto em cada categoria, do maior para o menor, e o total de
entradas por categoria.

**Why this priority**: é a visão principal pedida no briefing: descobrir onde se gasta mais.

**Independent Test**: com gastos em três categorias, conferir a lista ordenada e que a soma das
categorias bate com o total de saídas.

**Acceptance Scenarios**:

1. **Given** gastos de R$ 800,00 e R$ 200,00 em Alimentação e R$ 1.500,00 em Moradia, **When**
   peço o resumo, **Then** as saídas por categoria são Moradia R$ 1.500,00 e Alimentação
   R$ 1.000,00, nessa ordem.
2. **Given** categorias sem nenhum lançamento realizado no ciclo, **When** peço o resumo,
   **Then** elas não aparecem.
3. **Given** qualquer ciclo, **When** peço o resumo, **Then** a soma das saídas por categoria é
   igual ao total de saídas e a soma das entradas por categoria é igual ao total de entradas.
4. **Given** duas categorias com o mesmo total, **When** peço o resumo, **Then** elas aparecem
   em ordem alfabética.

---

### Edge Cases

- Ciclo só com o salário: entradas = salário, saídas = 0, saldo = salário, nenhuma saída por
  categoria.
- Categoria desativada depois de receber lançamentos continua aparecendo no resumo com seu nome.
- Data sem ciclo (antes do primeiro salário ou sem salário): o sistema informa que não há ciclo.
- O ciclo aberto é resumido com todos os lançamentos a partir do seu início, inclusive com data
  futura (desde que realizados).
- Um usuário nunca vê o resumo de outro.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST mostrar, para o ciclo que contém uma data, o total de entradas, o
  total de saídas e o saldo (entradas − saídas).
- **FR-002**: Os totais MUST considerar só lançamentos realizados e que contam no saldo.
- **FR-003**: O sistema MUST mostrar o total de saídas por categoria, do maior para o menor, e o
  total de entradas por categoria, na mesma ordem; empates em ordem alfabética.
- **FR-004**: Categorias sem lançamento que conte no ciclo MUST NOT aparecer.
- **FR-005**: A soma dos totais por categoria MUST ser igual ao total do respectivo tipo.
- **FR-006**: Todos os valores MUST ser em centavos inteiros.
- **FR-007**: O resumo MUST trazer as datas do ciclo (início, fim ou aberto, vizinhos) para
  navegação.
- **FR-008**: Data sem ciclo MUST responder que não há ciclo.
- **FR-009**: O resumo MUST usar só lançamentos do usuário autenticado.

### Key Entities

- **Resumo do ciclo** (derivado, não guardado): ciclo, total de entradas, total de saídas, saldo,
  totais por categoria de saída e de entrada.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: O resumo de um ciclo responde em menos de 1 segundo.
- **SC-002**: Em 100% dos resumos, saldo = entradas − saídas e a soma das categorias bate com os
  totais.
- **SC-003**: Nenhum lançamento previsto ou que não conta no saldo altera os totais.

## Assumptions

- Depende das features 001 (ciclo e lançamentos) e 002 (usuário autenticado).
- Nada é guardado: o resumo é calculado a cada consulta.
- Percentuais, comparação com o ciclo anterior e limites por categoria são P1/P2 e ficam fora.
- Lançamentos previstos pendentes (recorrências, parcelas) não aparecem no resumo; uma visão de
  "a pagar" é P1.
- Escopo só do backend.
