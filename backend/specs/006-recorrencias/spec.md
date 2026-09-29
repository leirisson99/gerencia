# Feature Specification: Gastos e Rendas Fixas (Recorrências)

**Feature Branch**: `006-recorrencias`

**Created**: 2026-09-29

**Status**: Draft

**Input**: Briefing P0: "Gastos fixos recorrentes gerados em cada ciclo, com confirmação de
pagamento". CLAUDE.md: "um previsto por recorrência em cada ciclo, na próxima ocorrência do dia
a partir do início do ciclo, gerado quando o ciclo abre".

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Cadastrar um gasto ou renda fixa (Priority: P1)

Cadastro uma vez algo que se repete todo mês (ex.: Internet, R$ 100,00, todo dia 10). Se já há
um ciclo aberto, o previsto deste ciclo aparece na hora.

**Why this priority**: sem o cadastro nada é gerado.

**Independent Test**: com um ciclo aberto desde 05/10, cadastrar "Internet" dia 10 e ver o
previsto de 10/10 nos lançamentos do ciclo.

**Acceptance Scenarios**:

1. **Given** um ciclo aberto desde 05/10/2026, **When** cadastro "Internet", R$ 100,00, Moradia,
   dia 10, **Then** existe um lançamento previsto de R$ 100,00 em 10/10/2026 ligado a ela.
2. **Given** o mesmo ciclo, **When** cadastro "Aluguel" dia 1, **Then** o previsto é 01/11/2026
   (a próxima ocorrência do dia 1 a partir de 05/10).
3. **Given** nenhum salário lançado, **When** cadastro uma recorrência, **Then** ela é salva e
   nenhum previsto é criado.
4. **Given** qualquer estado, **When** tento usar a categoria "Salário", dia fora de 1–31, valor
   não inteiro ou sem descrição, **Then** o sistema recusa com o motivo.

---

### User Story 2 - Previstos gerados quando o ciclo abre (Priority: P1)

Ao lançar o salário que abre um novo ciclo, cada recorrência ativa gera um previsto nele.

**Why this priority**: é o que tira do usuário o trabalho de relançar os fixos todo mês.

**Independent Test**: com duas recorrências, lançar o salário de 06/11 e ver os dois previstos
no novo ciclo.

**Acceptance Scenarios**:

1. **Given** "Internet" dia 10 e "Aluguel" dia 1, **When** lanço o salário de 06/11/2026,
   **Then** o novo ciclo tem previstos em 10/11/2026 e 01/12/2026.
2. **Given** um previsto do ciclo anterior ainda não confirmado, **When** o novo ciclo abre,
   **Then** ele continua no ciclo anterior, sem mudar nem duplicar.
3. **Given** uma recorrência desativada, **When** o ciclo abre, **Then** nada é gerado para ela.
4. **Given** um salário com data anterior ao mais recente (lançado depois), **When** é salvo,
   **Then** nenhum previsto é gerado.
5. **Given** um segundo salário na mesma data do mais recente, **When** é salvo, **Then** nenhum
   previsto é duplicado.

---

### User Story 3 - Confirmar o pagamento (Priority: P1)

Quando pago, confirmo o previsto (e ajusto valor ou data se mudou). Só então ele entra no saldo.

**Why this priority**: o saldo só conta o que aconteceu.

**Independent Test**: confirmar o previsto da Internet e ver o resumo do ciclo contá-lo.

**Acceptance Scenarios**:

1. **Given** o previsto da Internet, **When** o marco como realizado, **Then** o resumo passa a
   contar R$ 100,00 em Moradia.
2. **Given** a conta veio R$ 110,00, **When** confirmo com o novo valor, **Then** o resumo conta
   R$ 110,00.

---

### User Story 4 - Alterar ou desativar uma recorrência (Priority: P2)

Mudo valor, dia, descrição ou categoria, ou desativo. A mudança vale para os próximos ciclos.

**Acceptance Scenarios**:

1. **Given** a Internet a R$ 100,00, **When** mudo para R$ 120,00, **Then** o previsto já gerado
   continua R$ 100,00 e o do próximo ciclo sai com R$ 120,00.
2. **Given** a Internet ativa, **When** desativo, **Then** o próximo ciclo não recebe previsto.

---

### Edge Cases

- Dia 29, 30 ou 31 em mês mais curto: usa o último dia do mês.
- Virada de ano: ciclo aberto em 20/12 com recorrência dia 5 → previsto em 05/01.
- Previsto não conta no saldo até ser confirmado.
- Recorrência de entrada (outra renda fixa) gera previsto de entrada.
- Recorrência de outro usuário responde como inexistente.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O usuário MUST poder cadastrar recorrências com descrição, valor, categoria e dia
  (1–31); o tipo vem da categoria.
- **FR-002**: A categoria "Salário" MUST NOT ser usada em recorrências.
- **FR-003**: Quando um salário abre o ciclo mais recente, o sistema MUST gerar um lançamento
  previsto por recorrência ativa, na próxima ocorrência do dia a partir do início do ciclo.
- **FR-004**: Ao cadastrar uma recorrência com ciclo aberto, o sistema MUST gerar o previsto
  dela nesse ciclo.
- **FR-005**: Cada recorrência MUST ter no máximo um lançamento gerado por ciclo.
- **FR-006**: Dia inexistente no mês MUST virar o último dia do mês.
- **FR-007**: Previstos MUST NOT contar no saldo até serem confirmados como realizados.
- **FR-008**: O usuário MUST poder alterar e desativar recorrências; lançamentos já gerados não
  mudam.
- **FR-009**: Recorrências e seus lançamentos MUST ser só do próprio usuário.

### Key Entities

- **Recorrência**: descrição, valor (centavos), categoria, tipo, dia do mês, ativa.
- **Lançamento previsto**: lançamento com status previsto ligado à recorrência que o gerou.

## Success Criteria *(mandatory)*

- **SC-001**: Lançar o salário gera todos os previstos do ciclo em menos de 1 segundo.
- **SC-002**: Em 100% dos ciclos, cada recorrência ativa tem exatamente um lançamento gerado.
- **SC-003**: Nenhum previsto altera o saldo antes de confirmado.

## Assumptions

- O salário não é recorrência (lançado à mão).
- Só abrir um ciclo novo (salário mais recente) gera previstos; corrigir a data de um salário
  não gera nem apaga previstos.
- Confirmar é editar o lançamento previsto (status realizado), usando a edição da feature 001.
- Sem exclusão de recorrência: desativar cumpre o papel.
- Escopo só do backend.
