# Feature Specification: Cartela de Poupança

**Feature Branch**: `008-cartela-poupanca`

**Created**: 2026-09-29

**Status**: Draft

**Input**: Briefing P0: "Cartela de poupança: criar meta, gerar casas com ajuste, marcar depósito,
ver progresso". Regras: N é o maior inteiro com `base × N(N+1)/2 ≤ meta`; o resto vira uma casa
de ajuste; a soma das casas é a meta; depósito gera saída na categoria "Poupança".

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Criar uma cartela (Priority: P1)

Crio uma meta (ex.: R$ 1.000,00) com valor base (padrão R$ 1,00). O sistema gera as casas
1×, 2×, 3×… a base e, se sobrar, uma casa de ajuste para fechar exatamente na meta.

**Why this priority**: é o módulo de poupança do produto.

**Acceptance Scenarios**:

1. **Given** meta R$ 1.378,00 e base R$ 1,00, **When** crio, **Then** há 52 casas de R$ 1 a
   R$ 52, sem ajuste.
2. **Given** meta R$ 1.000,00 e base R$ 1,00, **When** crio, **Then** há 44 casas (soma R$ 990)
   e uma casa de ajuste de R$ 10,00.
3. **Given** meta R$ 5.000,00 e base R$ 5,00, **When** crio, **Then** há 44 casas de R$ 5 a
   R$ 220 e ajuste de R$ 50,00.
4. **Given** meta menor que a base, valor não inteiro ou cartela com mais de 1.000 casas,
   **When** crio, **Then** o sistema recusa.

---

### User Story 2 - Marcar e desmarcar depósitos (Priority: P1)

Marco qualquer casa, em qualquer ordem. Cada depósito vira uma saída na categoria "Poupança" no
ciclo atual. Posso desmarcar se errei.

**Acceptance Scenarios**:

1. **Given** a casa de R$ 30,00, **When** a marco, **Then** ela fica depositada hoje e existe
   uma saída realizada de R$ 30,00 em "Poupança".
2. **Given** a casa já depositada, **When** a marco de novo, **Then** o sistema recusa.
3. **Given** uma casa depositada, **When** a desmarco, **Then** ela volta a ficar livre e a
   saída some.
4. **Given** nenhum salário lançado, **When** marco uma casa, **Then** o sistema pede o salário
   (o depósito é um lançamento do ciclo).
5. **Given** o lançamento do depósito, **When** tento excluí-lo ou mudar valor ou categoria
   diretamente, **Then** o sistema recusa (use desmarcar).

---

### User Story 3 - Ver o progresso (Priority: P1)

Vejo o total guardado, quanto falta, o percentual e a maior casa ainda livre.

**Acceptance Scenarios**:

1. **Given** meta R$ 1.000,00 com as casas R$ 44 e R$ 10 (ajuste) depositadas, **When** consulto,
   **Then** guardado R$ 54,00, faltam R$ 946,00, 5%, maior livre R$ 43,00.
2. **Given** todas as casas depositadas, **Then** falta R$ 0,00, 100% e nenhuma casa livre.

---

### Edge Cases

- A soma das casas é sempre exatamente a meta.
- "Poupança" é categoria do sistema: não muda de nome nem é desativada.
- Cartela e casas de outro usuário respondem como inexistentes.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O usuário MUST poder criar cartelas com nome, meta e valor base (padrão R$ 1,00).
- **FR-002**: As casas MUST ser base × 1…N, com N o maior inteiro com `base × N(N+1)/2 ≤ meta`,
  mais uma casa de ajuste com o resto quando ele for maior que zero; a soma MUST ser a meta.
- **FR-003**: Meta menor que a base MUST ser recusada; cartelas com mais de 1.000 casas MUST
  ser recusadas.
- **FR-004**: Marcar uma casa MUST gerar um lançamento de saída realizado, com a data de hoje,
  na categoria de sistema "Poupança", e registrar a data do depósito.
- **FR-005**: Desmarcar MUST remover o lançamento e liberar a casa.
- **FR-006**: O lançamento de depósito MUST NOT ser excluído nem ter valor, status ou categoria
  alterados diretamente.
- **FR-007**: O progresso MUST mostrar guardado, falta, percentual (inteiro, arredondado para
  baixo) e a maior casa livre.
- **FR-008**: Todo usuário MUST ter a categoria de sistema "Poupança" (saída).
- **FR-009**: Cartelas MUST ser só do próprio usuário.

### Key Entities

- **Cartela**: nome, meta, valor base, criada em.
- **Casa**: valor, ordem, se é ajuste, data do depósito, lançamento do depósito.

## Success Criteria *(mandatory)*

- **SC-001**: Em 100% das cartelas, a soma das casas é igual à meta.
- **SC-002**: Cada depósito aparece uma única vez no saldo do ciclo.
- **SC-003**: Criar uma cartela de 1.000 casas responde em menos de 1 segundo.

## Assumptions

- Sem prazo e sem exclusão de cartela no P0.
- O depósito usa a data de hoje (São Paulo); não há escolha de data.
- Escopo só do backend.
