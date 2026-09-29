# Feature Specification: Categorias Editáveis

**Feature Branch**: `005-categorias`

**Created**: 2026-09-29

**Status**: Draft

**Input**: Briefing P0: "Categorias (lista inicial pronta, editável)". Próximo passo da lista:
"criar, renomear e desativar; hoje só existem as 8 iniciais".

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Criar uma categoria (Priority: P1)

Crio uma categoria de entrada ou de saída que não está na lista inicial (ex.: "Pets").

**Why this priority**: a lista inicial não cobre todos os gastos (hipótese H4 do briefing).

**Independent Test**: criar "Pets" como saída e lançar um gasto nela.

**Acceptance Scenarios**:

1. **Given** um usuário logado, **When** cria "Pets" do tipo saída, **Then** a categoria aparece na
   lista e aceita lançamentos.
2. **Given** a categoria "Moradia", **When** tenta criar "moradia" ou " Moradia ", **Then** o
   sistema recusa: já existe uma categoria com esse nome.
3. **Given** qualquer estado, **When** envia nome vazio, com mais de 60 caracteres ou tipo
   diferente de entrada/saída, **Then** o sistema recusa com o motivo.

---

### User Story 2 - Renomear uma categoria (Priority: P1)

Troco o nome de uma categoria; os lançamentos dela continuam ligados a ela.

**Why this priority**: ajustar a lista inicial ao próprio vocabulário.

**Independent Test**: renomear "Outros" para "Diversos" e ver o resumo do ciclo usar o novo nome.

**Acceptance Scenarios**:

1. **Given** "Outros" com lançamentos, **When** renomeio para "Diversos", **Then** a lista e o
   resumo mostram "Diversos" e os lançamentos continuam nela.
2. **Given** "Lazer" e "Saúde", **When** tento renomear "Lazer" para "saúde", **Then** o sistema
   recusa pelo nome repetido.
3. **Given** a categoria "Salário", **When** tento renomeá-la, **Then** o sistema recusa: é uma
   categoria do sistema.

---

### User Story 3 - Desativar e reativar (Priority: P1)

Desativo uma categoria que não uso; ela some da lista e não aceita novos lançamentos, mas os
lançamentos antigos continuam. Posso reativá-la.

**Why this priority**: limpa a lista sem perder histórico.

**Independent Test**: desativar "Transporte", ver que some da lista e recusa lançamento; ver que
aparece ao pedir as inativas; reativar.

**Acceptance Scenarios**:

1. **Given** "Transporte" ativa, **When** desativo, **Then** some da lista padrão e recusa novos
   lançamentos; os antigos continuam no resumo.
2. **Given** "Transporte" inativa, **When** peço a lista com as inativas, **Then** ela aparece
   marcada como inativa; **When** reativo, **Then** volta à lista padrão.
3. **Given** a categoria "Salário", **When** tento desativá-la, **Then** o sistema recusa.

---

### Edge Cases

- O tipo de uma categoria não muda depois de criada (os lançamentos copiam o tipo).
- Nome comparado sem diferenciar maiúsculas e ignorando espaços nas pontas.
- Categoria de outro usuário responde como inexistente.
- Criar uma categoria chamada "Salário" é recusado (o nome já existe).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O usuário MUST poder criar categorias com nome (1–60 caracteres) e tipo (entrada ou
  saída).
- **FR-002**: Nomes MUST ser únicos por usuário, sem diferenciar maiúsculas e sem espaços nas
  pontas.
- **FR-003**: O usuário MUST poder renomear e desativar/reativar suas categorias; o tipo MUST NOT
  mudar.
- **FR-004**: A categoria de sistema "Salário" MUST NOT ser renomeada nem desativada.
- **FR-005**: Categoria inativa MUST NOT aceitar novos lançamentos nem mudança de lançamento para
  ela; lançamentos existentes continuam valendo.
- **FR-006**: A lista padrão MUST mostrar só as ativas; a lista com inativas MUST indicar quais
  estão inativas.
- **FR-007**: Categoria de outro usuário MUST responder como inexistente.

### Key Entities

- **Categoria**: nome, tipo, ativa, sistema; pertence a um usuário.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Criar, renomear ou desativar responde em menos de 1 segundo.
- **SC-002**: 100% das tentativas de nome repetido são recusadas, inclusive simultâneas.
- **SC-003**: Nenhum lançamento é perdido ou muda de categoria ao renomear ou desativar.

## Assumptions

- Sem exclusão de categoria: desativar cumpre o papel sem perder histórico.
- Sem limite de quantidade de categorias.
- Escopo só do backend.
