# Feature Specification: Painel do Administrador

**Feature Branch**: `004-painel-admin`

**Created**: 2026-09-28

**Status**: Draft

**Input**: "podemos ter um painel de administrador onde podemos resetar a senha dos usuarios";
"vamos começar com o passo 1 e 2 só" (só reset de senha); "vamos deixar apenas para um
administrador por enquanto".

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Criar o administrador no servidor (Priority: P1)

Quem opera o servidor cria a conta de administrador com um comando. O sistema gera uma senha
temporária, mostra uma única vez e exige a troca no primeiro login. Só existe um administrador.

**Why this priority**: sem administrador ninguém pode resetar senhas; e ele não pode nascer do
cadastro público.

**Independent Test**: rodar o comando, entrar com a senha exibida, ver que a troca é exigida;
rodar o comando de novo e ver a recusa.

**Acceptance Scenarios**:

1. **Given** nenhum administrador, **When** o comando é executado com nome, e-mail, telefone e
   cargo, **Then** a conta é criada e uma senha temporária é exibida uma vez.
2. **Given** o administrador recém-criado, **When** ele entra, **Then** precisa trocar a senha
   antes de qualquer outra ação.
3. **Given** um administrador já existente, **When** o comando é executado de novo, **Then** o
   sistema recusa: só existe um administrador.
4. **Given** um e-mail já usado por outra conta, **When** o comando é executado com ele, **Then**
   o sistema recusa.

---

### User Story 2 - Encontrar a conta de quem pediu ajuda (Priority: P1)

Logado como administrador, listo as contas de usuários e busco por nome ou e-mail. Vejo só nome,
e-mail e data de criação.

**Why this priority**: é preciso achar a conta antes de resetar a senha.

**Independent Test**: com três usuários, listar e buscar por parte do nome e do e-mail.

**Acceptance Scenarios**:

1. **Given** usuários Ana, Bia e Caio, **When** o administrador lista as contas, **Then** vê os
   três em ordem alfabética, cada um com nome, e-mail e data de criação, e nada mais.
2. **Given** os mesmos usuários, **When** busca "bi" ou "BIA@", **Then** vê só a Bia.
3. **Given** um usuário comum logado, **When** tenta listar as contas, **Then** o acesso é negado.

---

### User Story 3 - Resetar a senha de um usuário (Priority: P1)

O administrador reseta a senha de uma conta. O sistema gera uma senha temporária, mostra uma
única vez, encerra as sessões do usuário e obriga a troca no próximo login. A ação fica
registrada.

**Why this priority**: é a única forma de recuperar o acesso, já que não há recuperação por
e-mail.

**Independent Test**: resetar a senha da Ana, ver a sessão aberta dela cair, entrar com a senha
temporária e ser obrigada a trocá-la.

**Acceptance Scenarios**:

1. **Given** a Ana logada num navegador, **When** o administrador reseta a senha dela, **Then**
   recebe uma senha temporária e a sessão da Ana deixa de funcionar.
2. **Given** o reset feito, **When** a Ana entra com a senha antiga, **Then** o login falha; com
   a temporária, entra e só consegue trocar a senha ou sair.
3. **Given** o reset feito, **Then** existe um registro com quem resetou, de quem e quando.
4. **Given** um usuário comum, **When** tenta resetar a senha de alguém, **Then** o acesso é
   negado e nada muda.
5. **Given** uma conta inexistente ou a do próprio administrador, **When** o reset é pedido,
   **Then** o sistema responde que a conta não foi encontrada.

---

### Edge Cases

- O administrador não vê dados financeiros nem telefone, cargo e data de nascimento de ninguém.
- O administrador não escolhe a senha de ninguém; a temporária é sempre gerada pelo sistema.
- A senha temporária segue a mesma regra de senha do cadastro.
- Resetar duas vezes: vale só a última senha temporária.
- Administrador com troca de senha pendente só troca a senha ou sai.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O administrador MUST ser criado só por comando no servidor, nunca pelo cadastro.
- **FR-002**: MUST existir no máximo um administrador.
- **FR-003**: A criação MUST gerar uma senha temporária, exibida uma única vez, e marcar a troca
  de senha como obrigatória.
- **FR-004**: Só o administrador MUST acessar a listagem e o reset; outros recebem acesso negado.
- **FR-005**: A listagem MUST mostrar só nome, e-mail e data de criação de contas de usuário
  comum, em ordem alfabética, com busca por parte do nome ou do e-mail sem diferenciar
  maiúsculas.
- **FR-006**: O reset MUST gerar uma senha temporária aleatória que cumpre a regra de senha,
  exibida uma única vez ao administrador.
- **FR-007**: O reset MUST encerrar todas as sessões do usuário e obrigar a troca de senha no
  próximo login.
- **FR-008**: Toda ação administrativa MUST ser registrada com quem fez, a ação, em quem e
  quando.
- **FR-009**: O administrador MUST NOT ter acesso a dados financeiros nem aos demais dados
  pessoais dos usuários.

### Key Entities

- **Administrador**: conta com papel de administrador; única.
- **Ação administrativa**: registro de auditoria (administrador, ação, usuário alvo, data e hora).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Resetar uma senha leva uma única ação do administrador e responde em menos de 1
  segundo.
- **SC-002**: 100% dos resets derrubam as sessões abertas do usuário.
- **SC-003**: 100% das ações administrativas ficam registradas.
- **SC-004**: Nenhuma resposta ao administrador contém dado financeiro, telefone, cargo ou data
  de nascimento.

## Assumptions

- Um único administrador por enquanto (decisão do usuário); a regra fica no escopo, não na
  constituição.
- A conta de administrador serve só para administração: o comando não cria categorias para ela.
- O usuário pede ajuda ao administrador por fora do sistema.
- Desativar ou reativar contas fica fora (decisão do usuário).
- Escopo só do backend; o "painel" é o conjunto de rotas administrativas.
- Emenda de 2026-09-29: quem opera o servidor pode recuperar o acesso do administrador com o
  comando `resetar-senha-admin` (nova senha temporária, sessões encerradas, troca obrigatória),
  já que não há recuperação por e-mail e só existe um administrador.
