# Feature Specification: Projeção do Ciclo

**Feature Branch**: `010-projecao-ciclo`

**Created**: 2026-09-29

**Status**: Draft

**Input**: Pedido explícito do usuário (item P2 do Briefing, "Projeção de fluxo de caixa"), com
escopo decidido em 2026-09-29: projetar só dentro do ciclo, sem prever o próximo salário.
"Quanto vai sobrar neste ciclo se tudo o que está previsto acontecer?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ver quanto vai sobrar no fim do ciclo (Priority: P1)

No resumo do ciclo, além do saldo do que já aconteceu, vejo quanto ainda está previsto para entrar
e para sair (gastos fixos e parcelas ainda não confirmados) e o saldo projetado: quanto sobra se
tudo o que está previsto acontecer.

**Why this priority**: o saldo realizado engana no meio do ciclo, porque o aluguel e as parcelas
ainda não saíram. O saldo projetado responde "quanto posso gastar ou guardar de verdade".

**Independent Test**: com salário de R$ 5.000,00, R$ 1.000,00 gastos, aluguel previsto de
R$ 1.500,00 e uma parcela prevista de R$ 200,00 a receber, pedir o resumo e conferir os totais.

**Acceptance Scenarios**:

1. **Given** um ciclo com saldo realizado de R$ 4.000,00, uma saída prevista de R$ 1.500,00 e uma
   entrada prevista de R$ 200,00, **When** peço o resumo, **Then** vejo saídas previstas
   R$ 1.500,00, entradas previstas R$ 200,00 e saldo projetado R$ 2.700,00.
2. **Given** um ciclo sem nenhum previsto, **When** peço o resumo, **Then** as previsões são zero e
   o saldo projetado é igual ao saldo.
3. **Given** uma parcela prevista de dívida paga no cartão (não conta no saldo), **When** peço o
   resumo, **Then** ela não entra nas previsões, porque o dinheiro sai pela fatura.
4. **Given** saídas previstas maiores que o saldo, **When** peço o resumo, **Then** o saldo
   projetado é negativo.
5. **Given** a saída prevista de R$ 1.500,00, **When** confirmo o pagamento com o mesmo valor,
   **Then** ela sai das previsões e entra nas saídas realizadas, e o saldo projetado não muda.
6. **Given** a saída prevista de R$ 1.500,00, **When** confirmo o pagamento com R$ 1.550,00,
   **Then** o saldo projetado diminui R$ 50,00.
7. **Given** um previsto com data em outro ciclo, **When** peço o resumo deste ciclo, **Then** ele
   não entra nas previsões deste ciclo.

---

### User Story 2 - Ver o que ainda vai sair em cada categoria (Priority: P2)

Na lista de saídas por categoria, cada categoria mostra também quanto ainda está previsto sair
nela, para eu ver onde está o peso do que falta pagar.

**Why this priority**: detalha a US1; o saldo projetado sozinho já entrega o valor principal.

**Independent Test**: com aluguel previsto em Moradia e internet prevista em Outros, conferir o
previsto de cada categoria e que a soma bate com o total de saídas previstas.

**Acceptance Scenarios**:

1. **Given** Moradia com R$ 1.500,00 previstos e nada realizado, **When** peço o resumo, **Then**
   Moradia aparece com total R$ 0,00 e previsto R$ 1.500,00.
2. **Given** Alimentação com R$ 800,00 realizados e nada previsto, **When** peço o resumo, **Then**
   Alimentação aparece com previsto R$ 0,00.
3. **Given** qualquer ciclo, **When** peço o resumo, **Then** a soma dos previstos por categoria é
   igual ao total previsto do respectivo tipo, e a soma dos totais realizados por categoria
   continua igual ao total realizado.
4. **Given** uma categoria com limite (feature 009), **When** ela tem previstos, **Then** a situação
   do limite continua calculada só com o realizado.

---

### Edge Cases

- Ciclo fechado com previstos que ficaram pendentes (fixo nunca confirmado): o resumo mostra esses
  previstos e o saldo projetado do ciclo; nada é movido para o ciclo seguinte.
- Previsto com data futura dentro do ciclo aberto conta normalmente.
- Categoria desativada com previsto pendente aparece com seu nome.
- A ordem das listas por categoria continua pelo total realizado (maior primeiro); empate por nome.
  Categorias só com previsto (total zero) vêm depois das com gasto realizado.
- Excluir um previsto o tira das previsões na próxima consulta.
- Um usuário nunca vê as previsões de outro.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O resumo do ciclo MUST mostrar o total de entradas previstas e o total de saídas
  previstas do ciclo.
- **FR-002**: Previsões MUST considerar só lançamentos previstos que contam no saldo, com data
  dentro do ciclo.
- **FR-003**: O resumo MUST mostrar o saldo projetado = saldo realizado + entradas previstas −
  saídas previstas.
- **FR-004**: Os totais realizados, o saldo e a situação dos limites MUST continuar como antes, sem
  incluir previstos.
- **FR-005**: Cada categoria nas listas por categoria MUST mostrar o total previsto além do total
  realizado; categorias só com previsto MUST aparecer, com total realizado zero.
- **FR-006**: A soma dos previstos por categoria MUST ser igual ao total previsto do tipo.
- **FR-007**: O sistema MUST NOT prever salários nem datas de ciclos futuros; a projeção vale só
  dentro do ciclo consultado.
- **FR-008**: Todos os valores MUST ser em centavos inteiros.
- **FR-009**: As previsões MUST usar só lançamentos do usuário autenticado.

### Key Entities

- **Projeção do ciclo** (derivada, não guardada): entradas previstas, saídas previstas e saldo
  projetado, calculados a partir dos lançamentos previstos do ciclo.
- **Previsto por categoria** (derivado): total previsto de uma categoria no ciclo.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em 100% dos resumos, saldo projetado = saldo + entradas previstas − saídas previstas.
- **SC-002**: Confirmar um previsto pelo mesmo valor nunca muda o saldo projetado.
- **SC-003**: Nenhuma parcela paga no cartão entra na projeção.
- **SC-004**: O resumo com projeção continua respondendo em menos de 1 segundo.

## Assumptions

- Pedido explícito do usuário em 2026-09-29, item P2 do Briefing (Princípio VI).
- Depende das features 003 (resumo), 006 (recorrências), 007 (dívidas) e 009 (limites).
- Projeção de ciclos futuros ou por mês de calendário fica fora: exigiria prever a data do salário
  (Princípio II).
- Os previstos já existem no sistema (gerados por recorrências e dívidas); esta feature só os lê.
- A projeção entra no resumo que já existe; não há consulta separada.
- O frontend mostra o saldo projetado e os previstos por categoria no painel do ciclo.
