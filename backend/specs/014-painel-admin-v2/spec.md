# Feature Specification: Painel do Administrador v2

**Feature Branch**: `014-painel-admin-v2`

**Created**: 2026-09-30

**Status**: Draft

**Input**: "preciso saber a quantidade de usuarios cadastrados, listar os usuarios, desativar
usuario, total de movimentações, grafico de movimentações por tipo, tipo de pagamento mais
usados". Decisões do usuário: só contagens globais (sem valores e sem nada por usuário);
"tipo de pagamento" = forma de pagamento das dívidas; gráfico = entradas × saídas por mês;
desativar bloqueia e é reversível. Constituição 5.0.0.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Desativar e reativar uma conta (Priority: P1)

O administrador desativa uma conta: as sessões dela caem e o login passa a ser recusado. Os
dados ficam guardados. Ele pode reativar a conta depois. As duas ações ficam registradas.

**Independent Test**: desativar a Ana com ela logada, ver a sessão cair e o login ser recusado;
reativar e ver o login voltar a funcionar com a mesma senha.

**Acceptance Scenarios**:

1. **Given** a Ana logada, **When** o administrador desativa a conta, **Then** a sessão dela
   deixa de funcionar e a conta aparece como desativada na lista.
2. **Given** a Ana desativada, **When** ela entra com a senha certa, **Then** o login é
   recusado com a mensagem de conta desativada; com a senha errada, a resposta é a de
   credenciais inválidas, como para qualquer conta.
3. **Given** a Ana desativada, **When** o administrador reativa, **Then** ela entra com a
   mesma senha e vê os mesmos dados.
4. **Given** uma conta já desativada, **When** é desativada de novo, **Then** nada muda e
   nenhum registro novo é criado (o mesmo vale para reativar uma conta ativa).
5. **Given** uma conta inexistente ou a do próprio administrador, **Then** a resposta é 404.
6. **Given** um usuário comum, **When** tenta desativar alguém, **Then** o acesso é negado.

---

### User Story 2 - Ver e filtrar as contas (Priority: P1)

A lista de contas mostra também a situação (ativa ou desativada) e pode ser filtrada por ela,
além da busca por nome ou e-mail.

**Acceptance Scenarios**:

1. **Given** Ana ativa e Bia desativada, **When** o administrador filtra por desativadas,
   **Then** vê só a Bia; por ativas, só a Ana; sem filtro, as duas.

---

### User Story 3 - Resumo de uso do sistema (Priority: P1)

O administrador vê, somado entre todos os usuários: quantas contas existem (ativas e
desativadas), quantos lançamentos existem (realizados e previstos), quantas entradas e saídas
realizadas houve em cada um dos últimos 12 meses e quantas dívidas existem por forma de
pagamento, da mais usada para a menos usada.

**Acceptance Scenarios**:

1. **Given** três contas, uma desativada, **Then** o resumo mostra 3 contas, 2 ativas e 1
   desativada; o administrador não conta.
2. **Given** lançamentos de dois usuários, **Then** o total soma os dois e separa realizados e
   previstos.
3. **Given** entradas e saídas realizadas em meses diferentes, **Then** cada mês dos últimos 12
   (o atual incluído) traz as quantidades; meses sem movimento aparecem com zero; previstos não
   entram no gráfico.
4. **Given** dívidas em pix e cartão, **Then** as quatro formas aparecem, ordenadas pela
   quantidade, com zero nas não usadas.
5. **Then** nenhuma parte do resumo traz valor em reais nem identifica usuários.

### User Story 4 - Mais indicadores de uso (Priority: P1)

Pedido em 2026-10-01 ("adicionar mais informações KPIs para a análise do administrador"),
grupos escolhidos: crescimento e engajamento, uso das funcionalidades e perfil por tipo de
renda. Tudo somado entre as contas de usuário comum, sem valores e sem nada por conta
(constituição 5.2.0).

**Acceptance Scenarios**:

1. **Given** contas criadas em meses diferentes, **Then** o resumo traz os cadastros de cada
   um dos últimos 12 meses (o atual incluído), com zero nos meses sem cadastro.
2. **Given** contas com último acesso há 2, 10 e 40 dias e uma que nunca entrou, **Then**
   ativas em 7 dias = 1 e em 30 dias = 2.
3. **Given** o login ou o uso de uma sessão, **Then** o último acesso da conta passa a ser
   hoje; mais acessos no mesmo dia (horário de São Paulo) não gravam de novo.
4. **Given** duas de três contas com lançamento, **Then** contas com lançamento = 2.
5. **Given** contas usando recorrências, dívidas, cartelas, serviços e importação, **Then**
   cada funcionalidade traz quantas contas distintas a usam (uma conta com dois usos conta
   uma vez).
6. **Given** lançamentos com e sem `id_externo`, **Then** o resumo separa importados e
   manuais.
7. **Given** contas `clt`, `prestador` e `clt_prestador`, **Then** o resumo traz quantas são
   de cada tipo, sempre os três.
8. **Then** o último acesso não aparece na lista de contas nem em nenhuma resposta por conta.

---

### Edge Cases

- Desativar não apaga nem altera dados financeiros.
- Resetar a senha de uma conta desativada continua permitido; ela segue sem entrar até ser
  reativada.
- Sessão de conta desativada que escape da limpeza é recusada como não autenticada.

## Requirements *(mandatory)*

- **FR-001**: O administrador MUST poder desativar e reativar contas de usuário comum.
- **FR-002**: Desativar MUST encerrar todas as sessões da conta e recusar o login com o código
  `conta_desativada`, revelado só quando a senha está correta.
- **FR-003**: Desativar e reativar MUST ser registrados em `acao_admin` quando mudam a situação.
- **FR-004**: A lista de contas MUST trazer a situação e aceitar filtro por ela.
- **FR-005**: O resumo MUST trazer só contagens globais, sem valores em reais e sem
  identificar usuários.

## Success Criteria *(mandatory)*

- **SC-001**: 100% das desativações derrubam as sessões abertas.
- **SC-002**: Nenhuma resposta do resumo contém valor monetário ou id de usuário.

## Assumptions

- "Movimentações" = lançamentos. O gráfico conta só realizados, pela data do lançamento.
- "Tipo de pagamento" = `forma_pagamento` da dívida, contando dívidas (não parcelas).
- Escopo backend e frontend (`/admin`).
- US4: "ativas" conta pelo último acesso guardado a partir desta versão; antes do deploy não
  há histórico, então as contas antigas começam como "nunca entrou".
- US4: o administrador fica fora de todas as contagens.
