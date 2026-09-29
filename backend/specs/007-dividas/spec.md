# Feature Specification: Dívidas com Parcelas

**Feature Branch**: `007-dividas`

**Created**: 2026-09-29

**Status**: Draft

**Input**: Briefing P0: "Dívidas (eu devo / me devem) com geração de parcelas e marcação de
paga/recebida". Regras: parcelas geradas como lançamentos previstos; `valor_total // parcelas`
com o resto na última; parcela paga no cartão não conta no saldo.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Cadastrar uma dívida e gerar as parcelas (Priority: P1)

Cadastro algo que devo (parcelamento, empréstimo) ou que me devem, com pessoa, valor total,
número de parcelas, forma de pagamento, dia de vencimento e início. O sistema cria todas as
parcelas como lançamentos previstos.

**Why this priority**: é o que permite acompanhar "faltam 4 de 10" sem lançar cada parcela.

**Independent Test**: cadastrar R$ 1.000,00 em 3 parcelas e ver 333,33 + 333,33 + 333,34 em
meses seguidos.

**Acceptance Scenarios**:

1. **Given** um ciclo aberto desde 05/10/2026, **When** cadastro "Notebook", devo à Loja X,
   R$ 1.000,00 em 3 parcelas, Pix, vencimento dia 15, início 05/10/2026, **Then** existem
   parcelas previstas de R$ 333,33 (15/10), R$ 333,33 (15/11) e R$ 333,34 (15/12).
2. **Given** "me devem" R$ 300,00 em 2 vezes do João, **When** cadastro, **Then** as parcelas
   são previstos de entrada.
3. **Given** uma dívida paga no cartão, **When** cadastro, **Then** as parcelas não contam no
   saldo (o dinheiro sai pela fatura).
4. **Given** um início antes do primeiro salário, ou nenhum salário lançado, **When** cadastro,
   **Then** o sistema recusa como qualquer lançamento fora de ciclo.
5. **Given** categoria de tipo incompatível (devo em categoria de entrada), cartão em "me devem",
   parcelas fora de 1–120 ou valor menor que o número de parcelas, **When** cadastro, **Then** o
   sistema recusa.

---

### User Story 2 - Marcar parcela paga ou recebida (Priority: P1)

Marco uma parcela como paga (devo) ou recebida (me devem). Ela passa a contar no saldo, exceto
se foi no cartão.

**Acceptance Scenarios**:

1. **Given** a parcela 1 do Notebook (Pix), **When** a marco como paga, **Then** o resumo do
   ciclo conta R$ 333,33 de saída.
2. **Given** uma parcela no cartão, **When** a marco como paga, **Then** o saldo não muda.

---

### User Story 3 - Acompanhar a dívida (Priority: P1)

Vejo cada dívida com quantas parcelas foram pagas, o valor pago, o que falta e se está quitada.

**Acceptance Scenarios**:

1. **Given** o Notebook com 1 de 3 parcelas paga, **When** consulto, **Then** vejo 1 de 3,
   pago R$ 333,33, faltam R$ 666,67, não quitada.
2. **Given** todas as parcelas pagas, **Then** a dívida aparece quitada.

---

### Edge Cases

- Resto de centavos sempre na última parcela; 1 parcela = valor total.
- Vencimento 31 em mês curto: último dia do mês.
- Parcelas atravessam a virada de ano.
- Parcela não pode ser excluída nem trocar de categoria (a dívida ficaria inconsistente);
  valor, data e status podem ser ajustados.
- Dívida e parcelas de outro usuário respondem como inexistentes.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O usuário MUST poder cadastrar dívidas com descrição, pessoa, direção (devo/me
  devem), valor total, parcelas (1–120), forma de pagamento (Pix, boleto, cartão, dinheiro),
  dia de vencimento (1–31), data de início e categoria.
- **FR-002**: O cadastro MUST gerar todas as parcelas como lançamentos previstos: cada uma com
  `valor_total // parcelas` e o resto na última; a soma MUST ser igual ao valor total.
- **FR-003**: A 1ª parcela MUST vencer na próxima ocorrência do dia de vencimento a partir do
  início; as demais, no mesmo dia dos meses seguintes (último dia se o mês for curto).
- **FR-004**: Devo MUST usar categoria de saída; me devem, de entrada.
- **FR-005**: Parcelas no cartão MUST NOT contar no saldo; cartão só vale para "devo".
- **FR-006**: As parcelas MUST obedecer à regra de ciclo (nenhuma antes do primeiro salário).
- **FR-007**: O usuário MUST poder marcar cada parcela como paga/recebida.
- **FR-008**: O sistema MUST mostrar, por dívida, parcelas pagas, total de parcelas, valor
  pago, valor restante e se está quitada.
- **FR-009**: Parcelas MUST NOT ser excluídas nem mudar de categoria.
- **FR-010**: Dívidas e parcelas MUST ser só do próprio usuário.

### Key Entities

- **Dívida**: descrição, pessoa, direção, valor total, parcelas, forma de pagamento, dia de
  vencimento, início, categoria.
- **Parcela**: lançamento previsto ligado à dívida, com número da parcela.

## Success Criteria *(mandatory)*

- **SC-001**: Em 100% das dívidas, a soma das parcelas é igual ao valor total.
- **SC-002**: Nenhuma parcela no cartão altera o saldo.
- **SC-003**: Cadastrar uma dívida de 120 parcelas responde em menos de 1 segundo.

## Assumptions

- Marcar como paga é editar a parcela (status realizado) com a edição da feature 001.
- Sem exclusão ou edição da dívida em si no P0; resumo de dívidas (total devido/a receber) é P1.
- Escopo só do backend.
