# Feature Specification: Cadastro e Login de Usuários

**Feature Branch**: `002-cadastro-login`

**Created**: 2026-09-28

**Status**: Draft

**Input**: User description: "Cadastro e login de usuários com e-mail e senha. Cadastro com nome,
e-mail, telefone e cargo obrigatórios e data de nascimento opcional. Cargo é só informativo.
Usuário pode trocar a própria senha. Sem recuperação de senha por e-mail e sem verificação de
e-mail."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Criar conta (Priority: P1)

Uma pessoa acessa o sistema pela web, preenche nome, e-mail, telefone, cargo, senha e,
se quiser, data de nascimento, e passa a ter uma conta própria, já entrando no sistema.

**Why this priority**: sem conta ninguém usa o sistema; todo dado financeiro pertence a um
usuário.

**Independent Test**: cadastrar uma pessoa com dados válidos e ver que ela entra no sistema;
tentar cadastrar com dados faltando ou inválidos e ver cada recusa explicada.

**Acceptance Scenarios**:

1. **Given** nenhum cadastro com o e-mail `ana@exemplo.com`, **When** a pessoa informa nome "Ana
   Souza", e-mail `ana@exemplo.com`, telefone (11) 98765-4321, cargo "Desenvolvedora" e uma
   senha válida, sem data de nascimento, **Then** a conta é criada e ela já entra no sistema.
2. **Given** o mesmo cenário, **When** ela também informa a data de nascimento 15/03/1995,
   **Then** a conta é criada com essa data.
3. **Given** qualquer estado, **When** falta nome, e-mail, telefone, cargo ou senha, **Then** o
   sistema recusa e indica cada campo que falta.
4. **Given** uma conta com `ana@exemplo.com`, **When** alguém tenta cadastrar `ANA@Exemplo.com`,
   **Then** o sistema recusa informando que o e-mail já está cadastrado.
5. **Given** qualquer estado, **When** o e-mail tem formato inválido, o telefone não tem DDD +
   número, a senha é fraca ou a data de nascimento é futura, **Then** o sistema recusa e
   explica o motivo.
6. **Given** qualquer cadastro pelo formulário público, **When** a conta é criada, **Then** ela
   é sempre de usuário comum, nunca de administrador.

---

### User Story 2 - Entrar e sair (Priority: P1)

Com a conta criada, entro com e-mail e senha em qualquer navegador e saio quando quiser.

**Why this priority**: sem login a pessoa não volta aos próprios dados.

**Independent Test**: entrar com credenciais corretas, ver os próprios dados, sair e ver que o
acesso foi encerrado; tentar entrar com senha errada e ver a recusa.

**Acceptance Scenarios**:

1. **Given** uma conta `ana@exemplo.com`, **When** ela entra com e-mail e senha corretos, **Then**
   acessa o sistema.
2. **Given** a mesma conta, **When** ela entra com senha errada ou com um e-mail inexistente,
   **Then** o sistema responde a mesma mensagem genérica "e-mail ou senha inválidos".
3. **Given** 5 tentativas de login erradas seguidas para o mesmo e-mail em 15 minutos, **When**
   tentam de novo, **Then** o sistema bloqueia novas tentativas para esse e-mail por 15 minutos,
   mesmo com a senha certa.
4. **Given** uma pessoa logada, **When** ela sai, **Then** qualquer ação seguinte exige entrar
   de novo.
5. **Given** ninguém logado, **When** alguém tenta acessar qualquer dado do sistema, **Then** o
   acesso é negado e a pessoa é orientada a entrar.

---

### User Story 3 - Trocar a própria senha (Priority: P1)

Logado, troco minha senha informando a senha atual e a nova.

**Why this priority**: sem recuperação por e-mail, trocar a senha é a única forma de o usuário
manter a conta segura; e é obrigatória depois de um reset pelo administrador (feature 003).

**Independent Test**: trocar a senha, sair e entrar com a nova; tentar com a senha atual errada
e ver a recusa.

**Acceptance Scenarios**:

1. **Given** uma pessoa logada, **When** informa a senha atual correta e uma nova senha válida,
   **Then** a senha é trocada e as outras sessões abertas dela são encerradas, mantendo a atual.
2. **Given** uma pessoa logada, **When** informa a senha atual errada, **Then** a troca é
   recusada.
3. **Given** uma pessoa logada, **When** a nova senha é fraca ou igual à atual, **Then** a troca
   é recusada com o motivo.
4. **Given** uma conta marcada com troca de senha obrigatória, **When** a pessoa entra, **Then**
   ela só consegue trocar a senha ou sair até concluir a troca.

---

### User Story 4 - Ver e editar os próprios dados (Priority: P2)

Logado, vejo meus dados de cadastro (nome, e-mail, telefone, cargo e data de nascimento) e
corrijo nome, telefone, cargo e data de nascimento. O e-mail não pode ser trocado.

**Why this priority**: útil para conferência e correção de erros, mas não bloqueia o uso do
sistema.

**Independent Test**: entrar e ver exatamente os dados informados no cadastro, sem a senha;
alterar o telefone e ver o novo valor; tentar alterar o e-mail e ver a recusa.

**Acceptance Scenarios**:

1. **Given** uma pessoa logada, **When** abre seus dados, **Then** vê nome, e-mail, telefone,
   cargo e data de nascimento (se informada), e nunca a senha.
2. **Given** duas contas, **When** uma tenta ver os dados da outra, **Then** o sistema responde
   como se a conta não existisse.
3. **Given** uma pessoa logada, **When** altera nome, telefone, cargo ou data de nascimento com
   valores válidos, **Then** os novos valores são salvos e exibidos.
4. **Given** uma pessoa logada, **When** tenta deixar nome, telefone ou cargo vazios, ou
   informa valores inválidos, **Then** a alteração é recusada com as mesmas regras do cadastro.
5. **Given** uma pessoa logada com data de nascimento informada, **When** a remove, **Then** a
   conta fica sem data de nascimento.
6. **Given** uma pessoa logada, **When** tenta alterar o e-mail, **Then** o sistema recusa.

---

### Edge Cases

- E-mail com espaços nas pontas ou letras maiúsculas é normalizado (sem espaços, minúsculo)
  antes de validar a unicidade e no login.
- Telefone digitado com ou sem máscara ((11) 98765-4321, 11987654321) é aceito e guardado só com
  os dígitos.
- Nome ou cargo só com espaços contam como vazios.
- Data de nascimento no futuro ou anterior a 1900 é recusada.
- Duas pessoas tentando cadastrar o mesmo e-mail ao mesmo tempo: só uma conta é criada.
- Esquecer a senha: não há recuperação por e-mail; a pessoa precisa pedir ao administrador
  (feature 003).
- Sessão parada por muito tempo expira e exige novo login.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Qualquer pessoa MUST poder criar uma conta informando nome, e-mail, telefone,
  cargo e senha (obrigatórios) e data de nascimento (opcional).
- **FR-002**: O e-mail MUST ser único entre todas as contas, comparado sem diferenciar
  maiúsculas e ignorando espaços nas pontas.
- **FR-003**: O telefone MUST ser brasileiro, com DDD e 10 ou 11 dígitos.
- **FR-004**: A senha MUST ter no mínimo 8 caracteres, com pelo menos uma letra e um número, e
  no máximo 128 caracteres.
- **FR-005**: O cargo MUST ser texto livre e só informativo; ele não dá nenhuma permissão.
- **FR-006**: Toda conta criada pelo cadastro público MUST ser de usuário comum.
- **FR-007**: Após o cadastro, a pessoa MUST entrar no sistema automaticamente.
- **FR-008**: O login MUST usar e-mail e senha e, em caso de falha, responder sempre a mesma
  mensagem genérica, sem revelar se o e-mail existe.
- **FR-009**: Após 5 falhas seguidas de login para um e-mail em 15 minutos, o sistema MUST
  bloquear novas tentativas desse e-mail por 15 minutos.
- **FR-010**: O usuário MUST poder sair, encerrando a sessão atual.
- **FR-011**: Sessões MUST expirar após 30 dias sem uso.
- **FR-012**: Todo acesso a dados, exceto cadastro e login, MUST exigir usuário logado.
- **FR-013**: O usuário MUST poder trocar a própria senha informando a senha atual; a nova senha
  segue FR-004 e MUST ser diferente da atual.
- **FR-014**: Ao trocar a senha, as outras sessões do usuário MUST ser encerradas.
- **FR-015**: Se a conta estiver marcada com troca de senha obrigatória, o usuário MUST só poder
  trocar a senha ou sair até concluir a troca, que remove a marcação.
- **FR-016**: A senha MUST ser guardada de forma irreversível e nunca exibida nem devolvida.
- **FR-017**: O usuário MUST poder ver os próprios dados de cadastro, e nunca os de outro
  usuário.
- **FR-017a**: O usuário MUST poder alterar o próprio nome, telefone, cargo e data de
  nascimento (inclusive removê-la), com as mesmas validações do cadastro; o e-mail MUST NOT
  ser alterável.
- **FR-018**: A criação da conta MUST criar a categoria de sistema "Salário" do usuário (exigida
  pela feature 001).

### Key Entities

- **Usuário**: pessoa com conta; nome, e-mail (único), telefone, cargo, data de nascimento
  (opcional), senha (guardada de forma irreversível), papel (usuário comum ou administrador),
  marcação de troca de senha obrigatória e data de criação.
- **Sessão**: acesso ativo de um usuário num navegador; tem início, último uso e pode ser
  encerrada.
- **Tentativa de login**: registro de falhas recentes por e-mail, usado para o bloqueio
  temporário.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: O cadastro responde, com sucesso ou com todos os erros indicados, em menos de 1
  segundo.
- **SC-002**: O login responde em menos de 1 segundo, com e-mail existente ou inexistente.
- **SC-003**: 100% das tentativas de acessar dados de outro usuário são recusadas.
- **SC-004**: Nenhuma resposta do sistema exibe a senha ou permite descobrir se um e-mail existe
  pelo login.
- **SC-005**: Após trocar a senha, 100% das outras sessões do usuário deixam de funcionar.

## Assumptions

- Sem recuperação de senha por e-mail e sem verificação de e-mail; quem esquecer a senha
  depende do administrador (feature 003). Qualquer e-mail com formato válido é aceito, mesmo
  que não pertença à pessoa.
- O cadastro público informa quando um e-mail já está cadastrado; sem verificação de e-mail,
  não há como evitar isso sem prejudicar o cadastro.
- O administrador não é criado por esta feature; a criação e o painel ficam na feature 003.
- Telefones são brasileiros; números internacionais ficam fora de escopo.
- Não há idade mínima para o cadastro.
- Fora de escopo: excluir a conta, trocar o e-mail, login social, autenticação em dois fatores.
- O sistema roda na web com banco PostgreSQL.
- Escopo só do backend: as telas de cadastro, login e perfil ficam fora desta feature; tudo é
  verificado pela API.
