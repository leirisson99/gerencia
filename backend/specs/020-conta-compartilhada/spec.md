# Feature Specification: Contas compartilhadas

**Feature Branch**: `020-conta-compartilhada`

**Created**: 2026-10-16

**Status**: Draft (clarificada em 2026-10-16)

**Input**: "módulo de dívida compartilhada: uma pessoa cadastra aluguel, água, luz com outras
pessoas para dividir uma parcela de cada valor; pagamento de um valor total". Decisões do
usuário: só se divide com usuários do app; cada conta tem seu número de pessoas (energia ÷ 6,
aluguel ÷ 4, água ÷ 3); o total sempre aparece. Convite por e-mail com aceite; só o dono edita;
a cota de cada participante vira lançamento previsto no saldo dele. Exige emenda MAJOR da
constituição (exceção ao isolamento por usuário).

## Exemplo de referência

Ana (dona) cadastra "Energia", dia 10, dividida por 6 (ela + 5 convidados), modo igual. Em
outubro informa o total: R$ 600,00. Cada uma das 6 pessoas tem cota de R$ 100,00 e um
lançamento previsto de R$ 100,00 no próprio saldo. A tela mostra: total R$ 600,00, 6 pessoas,
minha cota R$ 100,00. Com total R$ 100,00 ÷ 3 (água), as cotas são 33,33 / 33,33 / 33,34 (o
resto fica na última).

## Clarifications

### Session 2026-10-16

- Q: O que um participante aceito pode ver sobre os outros participantes? → A: Total, nº de
  pessoas e a própria cota; dos demais, só nome e status (pendente / informado / confirmado),
  sem e-mail nem valor.
- Q: O que acontece com convite para e-mail sem conta no app? → A: Aceita qualquer e-mail com
  resposta sempre igual (não revela se há conta); convite pendente por 30 dias, vinculado ao
  usuário quando o e-mail se cadastra; depois disso expira.
- Q: Qual o máximo de participantes por conta? → A: 20, contando o dono.
- Q: A confirmação do dono torna realizado o lançamento do participante? → A: Não. Cada pessoa
  realiza o próprio lançamento como hoje; o status da cota (pendente / informado / confirmado)
  é derivado do lançamento do próprio titular e da confirmação do dono, e nunca altera o saldo
  de ninguém.
- Q: O que acontece com a cobrança do mês quando um participante sai ou é removido? → A:
  Nada: a cobrança já gerada fica como está; a saída vale só da próxima cobrança.
- Q: A cobrança divide entre quem aceitou ou entre todos os convidados? → A: Só entre quem
  aceitou até a hora de gerar a cobrança; o número de pessoas é o de aceitos (6 era só um
  exemplo). Convidados pendentes não são cobrados; a tela mostra "aceitos de convidados". Nos
  modos percentual e fixo a soma é validada só entre os aceitos.
- Q: O participante pode excluir ou alterar o lançamento previsto da cota? → A: Não pode
  excluir nem alterar valor ou data (409, como a parcela de dívida). Só muda o status: realizar
  ("paguei") e cancelar, que desfaz o "paguei" (o lançamento volta a previsto e a cota volta a
  pendente). Categoria e descrição seguem livres. A cota em si nunca some.
- Q: O convite mostra o nome do dono a quem ainda não aceitou? → A: Sim. O convite mostra o
  nome do dono, a descrição da conta (ex.: "Energia") e a data do convite, sem
  valores nem e-mail. Constituição 8.1.0 (nome do dono visível ao
  convidado).
- Q: Quem sai ou é removido ainda recebe o lançamento das cobranças já geradas? → A: Sim. A
  cota de cobrança já gerada continua virando lançamento previsto no ciclo dele, mesmo sem
  acesso à conta; as cobranças futuras não o incluem.
- Q: Quem gera a cobrança de contas sem valor fixo (água, luz)? → A: Só o dono informa o total
  do mês. Conta de valor fixo gera sozinha quando qualquer participante aceito lê o ciclo
  (idempotente). Sem total informado, o dono vê o aviso "falta informar o total de [mês]".

### Session 2026-10-17

- Q: Em conta de valor fixo, quando a cobrança do mês é gerada? → A: O dono pode gerar quando
  quiser ("Gerar cobrança de [mês]"). Se não gerar, a conta gera sozinha a partir do dia de
  vencimento, na leitura de qualquer participante aceito, de forma idempotente. Assim o dono
  decide quando fechar a lista de aceitos.
- Q: Em percentual e fixo, qual é a parte do dono e como corrigir valores? → A: O dono define a
  própria parte, como a de qualquer participante (o dono também tem percentual ou valor). Se a
  soma entre os aceitos não fechar (percentual ≠ 100%, ou fixos ≠ total), a cobrança falha
  (422, com a diferença) até o dono corrigir; ele edita o valor de cada participante, inclusive
  o dele.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Cadastrar a conta e dividir (Priority: P1)

O dono cria a conta (descrição, categoria, dia de vencimento, valor fixo opcional), escolhe o
modo de divisão (igual, percentual ou valor fixo) e convida participantes por e-mail.

**Why this priority**: sem a conta e a divisão não existe o módulo.

**Independent Test**: Ana cria "Aluguel" com valor fixo R$ 2.000, convida 3 pessoas que aceitam
e gera a cobrança; a tela mostra total R$ 2.000, 4 pessoas e cota R$ 500 cada.

**Acceptance Scenarios**:

1. **Given** Ana e 2 convidados que aceitaram, **When** a cobrança de R$ 100 é gerada, **Then**
   as 3 cotas somam exatamente R$ 100 (resto na última).
2. **Given** modo percentual com soma ≠ 100%, **Then** é recusado.
3. **Given** modo fixo com soma dos valores dos aceitos ≠ total, **Then** é recusado (422).
4. **Given** a conta, **Then** o total e o número de pessoas (aceitas) aparecem sempre, junto
   de quantos convidados ainda não aceitaram.
5. **Given** 6 convidados e 3 aceites, **When** a cobrança é gerada, **Then** a divisão é entre
   os 3 aceitos; quem aceitar depois entra só nas cobranças seguintes.

### User Story 2 - Aceitar o convite (Priority: P1)

O convidado (usuário cadastrado) vê o convite, escolhe a categoria em que a cota entra e
aceita ou recusa.

**Independent Test**: Bia aceita o convite de Ana e passa a ver a conta; antes do aceite, a
conta responde "não encontrado".

**Acceptance Scenarios**:

1. **Given** convite pendente ou recusado, **Then** a pessoa não vê a conta (404), mas a
   lista de convites mostra o nome do dono, a descrição da conta e a data, sem valores.
2. **Given** convite aceito, **Then** vê total, nº de pessoas, a própria cota e o status, e
   dos demais só nome e status; nunca e-mail nem valor da cota de outro.
3. **Given** qualquer e-mail convidado, **Then** a resposta é a mesma exista conta ou não; o
   convite fica pendente por 30 dias e se vincula ao usuário quando o e-mail se cadastrar; após
   30 dias expira e o dono pode convidar de novo.
4. **Given** participante, **When** tenta editar a conta, **Then** é recusado.

### User Story 3 - Cobrança mensal e lançamentos (Priority: P1)

Conta com valor fixo gera a cobrança do mês sozinha; conta variável (água/luz) gera quando o
dono informa o total do mês. Cada participante aceito recebe um lançamento previsto da própria
cota, na própria categoria, só na carteira PF.

**Independent Test**: Ana informa R$ 600 de energia; as 6 pessoas ganham previsto de R$ 100; o
saldo e o gasto por categoria de cada uma contam apenas R$ 100.

**Acceptance Scenarios**:

1. **Given** uma competência já gerada, **When** gera de novo, **Then** nada é duplicado.
2. **Given** participante que entra depois, **Then** só vale para cobranças futuras (a
   cobrança já gerada não é refeita).
3. **Given** participante que sai ou é removido, **Then** a cobrança já gerada (cotas e
   lançamentos, inclusive o do mês corrente) não muda e o lançamento da cota dele continua
   sendo criado no ciclo dele; a saída vale a partir da próxima cobrança.

### User Story 4 - Pagamento da cota (Priority: P2)

O participante marca "paguei", que é realizar o lançamento da própria cota, ou cancela, que
desfaz isso; o dono confirma o recebimento. Estados da cota, derivados: pendente (lançamento
previsto ou ainda não criado) → informado (lançamento realizado) → confirmado (dono confirmou
e o lançamento está realizado).

**Acceptance Scenarios**:

1. **Given** cota pendente, **When** o participante realiza o próprio lançamento ("paguei"),
   **Then** a cota aparece como "informado".
2. **Given** "informado", **When** o dono confirma, **Then** vira "confirmado".
3. **Given** participante, **When** tenta confirmar, **Then** é recusado.
4. **Given** "informado" ou "confirmado", **When** o participante cancela (volta o lançamento
   para previsto), **Then** a cota volta a "pendente" e a confirmação deixa de valer.

## Requirements *(mandatory)*

- **FR-001**: Dinheiro em centavos inteiros; a soma das cotas é sempre igual ao total.
- **FR-001b**: A cobrança divide o total só entre os participantes `aceito` na hora de gerá-la
  (o dono sempre conta, com a própria parte). Percentual MUST somar 100% e fixo MUST somar o
  total, ambos entre os aceitos, na hora da cobrança; senão 422 com a diferença. Só o dono
  edita o valor de cada participante, inclusive o dele.
- **FR-001a**: Uma conta tem no máximo 20 participantes (dono incluído); acima disso o convite
  é recusado.
- **FR-002**: Acesso a uma conta = dono ou participante `aceito`; qualquer outro recebe 404.
- **FR-003**: Só o dono edita conta, participantes e valores; participante só aceita ou recusa,
  sai, e realiza ou desfaz a realização do próprio lançamento.
- **FR-004**: O lançamento gerado pertence ao próprio usuário da cota (nunca criado em outro
  usuário sem aceite), carteira PF, `conta_no_saldo=True`.
- **FR-004a**: Só o dono do saldo realiza ou desfaz a realização do próprio lançamento. O
  status da cota é derivado desse lançamento e da confirmação do dono; confirmar ou desfazer
  a confirmação nunca altera lançamento nem saldo de ninguém.
- **FR-004b**: O lançamento de uma cota MUST NOT ser excluído nem ter valor ou data alterados
  (409); o titular só realiza, desfaz a realização, ou muda categoria e descrição.
  Não é recriado: a cota guarda o vínculo enquanto existir.
- **FR-004c**: Cobrança de conta sem valor fixo só nasce quando o dono informa o total. A de
  conta com valor fixo nasce quando o dono a gera ou, se ele não gerar, a partir do dia de
  vencimento do mês, na leitura do ciclo de qualquer participante aceito, de forma idempotente.
  O dono vê "falta informar o total de [mês]" enquanto faltar.
- **FR-005**: A geração é idempotente (UNIQUE conta + competência; UNIQUE cobrança + participante).
- **FR-006**: Nenhuma coluna nova em `lancamento`, `divida` ou `recorrencia`; saldo e ciclo
  existentes não mudam.
- **FR-007**: O admin só vê contagens de uso, nunca valores, nomes ou e-mails.
- **FR-008**: O módulo não existe na carteira PJ.
- **FR-009**: Regra de domínio (`ratear`) nasce com teste.

## Out of scope (v1)

Contas em PJ, edição de cobrança já gerada, notificação push de convite, divisão entre
não-usuários, visão consolidada entre contas.
