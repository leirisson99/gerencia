# Feature Specification: Carteiras PF e PJ

**Feature Branch**: `019-carteira-pj`

**Created**: 2026-10-03

**Status**: Implementada (2026-10-03); falta validar no navegador (quickstart)

**Input**: "vamos implementar para PJ e pessoa física, esses módulos são essenciais para
abranger mais pessoas". Decisão do usuário: leitura A, ou seja, a pessoa que trabalha como PJ
(MEI ou ME) e precisa separar o dinheiro da empresa do dinheiro pessoal. Fase 1 sem visão
consolidada. Constituição 7.0.0.

## Exemplo de referência

Carlos é designer e MEI (`prestador`). Em outubro:

| Carteira | Data | Movimento | Valor |
| --- | --- | --- | --- |
| PJ | 05/10 | Cliente pagou | + R$ 8.000,00 |
| PJ | 20/10 | DAS | − R$ 75,00 |
| PJ | 20/10 | Contador | − R$ 300,00 |
| PJ | 25/10 | Retirada para PF | − R$ 5.000,00 |
| PF | 25/10 | Pró-labore e lucros | + R$ 5.000,00 |
| PF | 26/10 | Aluguel | − R$ 1.800,00 |
| PF | 28/10 | Mercado | − R$ 900,00 |

Saldo de outubro: PJ = R$ 2.625,00; PF = R$ 2.300,00. Os dois números aparecem separados e
nunca são somados.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ligar a carteira PJ e lançar nela (Priority: P1)

Quem é `prestador` ou `clt_prestador` liga "Tenho CNPJ" no perfil. Aparece o seletor PF | PJ.
Na PJ, a pessoa lança entradas e saídas da empresa e vê o saldo e o gasto por categoria do mês
do calendário, sem precisar de salário.

**Why this priority**: separar o dinheiro da empresa do pessoal é o problema central de quem é
PJ. Sem isso, nada mais da feature faz sentido.

**Independent Test**: Carlos liga a PJ, lança + R$ 8.000 (cliente), − R$ 75 (DAS) e − R$ 300
(contador) na PJ e vê saldo PJ de R$ 7.625 em outubro. O saldo PF não muda.

**Acceptance Scenarios**:

1. **Given** Carlos `prestador` sem PJ, **When** liga "Tenho CNPJ", **Then** passa a ver o
   seletor PF | PJ, com a PF aberta por padrão.
2. **Given** Ana `clt`, **When** tenta ligar a PJ, **Then** a ação é recusada com a orientação
   de mudar o tipo de renda para `clt_prestador`.
3. **Given** Carlos com PJ, **When** lança uma saída na PJ em 20/10, **Then** ela aparece só no
   ciclo PJ de outubro (01/10 a 31/10) e entra no saldo e no gasto por categoria da PJ.
4. **Given** Ana `clt_prestador` com PJ e sem nenhum salário lançado, **When** lança na PJ,
   **Then** o lançamento é aceito; na PF continua exigindo o salário primeiro.
5. **Given** qualquer pessoa com PJ, **When** tenta lançar "Salário" na PJ, **Then** é
   recusado com a orientação de usar a retirada.
6. **Given** um lançamento criado sem informar a carteira, **Then** ele fica na PF.
7. **Given** uma pessoa sem PJ ligada, **When** tenta lançar na PJ, **Then** é recusado.
8. **Given** o lançamento PJ de outro usuário, **Then** toda tentativa de vê-lo ou alterá-lo
   responde "não encontrado".

---

### User Story 2 - Retirar dinheiro da PJ para a PF (Priority: P1)

Na PJ, a pessoa usa "Retirar para PF", informa valor e data, e o sistema registra os dois
lados de uma vez: a saída na PJ e a entrada na PF.

**Why this priority**: é a ponte entre as duas carteiras. Sem ela, a pessoa teria de lançar
duas vezes e os lados poderiam ficar diferentes.

**Independent Test**: Carlos retira R$ 5.000 em 25/10. O saldo PJ de outubro cai R$ 5.000 e a
PF ganha uma entrada de R$ 5.000 em "Pró-labore e lucros" na mesma data.

**Acceptance Scenarios**:

1. **Given** Carlos com PJ, **When** retira R$ 5.000 em 25/10, **Then** surgem uma saída
   realizada na PJ ("Retirada para PF") e uma entrada realizada na PF ("Pró-labore e
   lucros"), ambas de R$ 5.000 em 25/10.
2. **Given** a retirada, **When** Carlos muda o valor para R$ 4.500 ou a data para 24/10,
   **Then** os dois lados mudam juntos.
3. **Given** a retirada, **When** Carlos a exclui, **Then** os dois lados somem juntos.
4. **Given** um dos lados da retirada, **When** Carlos tenta editá-lo ou excluí-lo pelo
   lançamento, **Then** é recusado com a orientação de alterar pela retirada.
5. **Given** uma retirada com data futura ou valor zero, **Then** é recusada.
6. **Given** Ana `clt_prestador` com PJ, **When** retira para uma data em que a PF não tem
   ciclo de salário, **Then** é recusada pelo mesmo motivo de um lançamento PF fora de ciclo.
7. **Given** retiradas de outro usuário, **Then** não aparecem e respondem "não encontrado".

---

### User Story 3 - Recorrências da empresa (Priority: P2)

A pessoa cadastra recorrências na PJ (DAS, contador, aluguel da sala). Cada uma gera o previsto
no mês do calendário, sem duplicar.

**Why this priority**: o DAS mensal é o gasto fixo mais comum de quem é PJ. Sem isso, a pessoa
lança à mão todo mês, mas a carteira já funciona.

**Independent Test**: Carlos cria a recorrência "DAS", R$ 75 no dia 20, na PJ. Ao abrir outubro
e novembro na PJ aparece um previsto de R$ 75 no dia 20 de cada mês, e nada na PF.

**Acceptance Scenarios**:

1. **Given** a recorrência PJ do dia 20, **When** a PJ de outubro é aberta duas vezes,
   **Then** existe um único previsto em 20/10.
2. **Given** a recorrência PJ, **Then** ela não gera nada na PF, mesmo para `clt_prestador`
   ao lançar o salário.
3. **Given** uma recorrência criada sem informar a carteira, **Then** ela é da PF.

---

### User Story 4 - Lembretes com as duas carteiras (Priority: P3)

A lista de lembretes junta contas e valores das duas carteiras, cada item marcado PF ou PJ.

**Independent Test**: com um previsto PJ e um PF vencendo amanhã, os dois aparecem nos
lembretes, cada um com sua marca.

**Acceptance Scenarios**:

1. **Given** o DAS previsto na PJ e o aluguel previsto na PF para amanhã, **Then** os dois
   aparecem nos lembretes, marcados PJ e PF.
2. **Given** o resumo diário por push, **Then** ele conta as duas carteiras juntas, sem
   valores nem nomes, como hoje.

---

### User Story 5 - Desligar a PJ e trocar o tipo de renda (Priority: P3)

**Acceptance Scenarios**:

1. **Given** Carlos com PJ e nenhum dado PJ, **When** desliga "Tenho CNPJ", **Then** o seletor
   some.
2. **Given** Carlos com lançamento, recorrência ou retirada na PJ, **When** tenta desligar a PJ
   ou trocar para `clt`, **Then** é recusado com a explicação do motivo.
3. **Given** Carlos com PJ, **When** troca de `prestador` para `clt_prestador`, **Then** a PJ
   continua ligada e os dados PJ não mudam; só as regras de ciclo da PF passam a valer as do
   novo tipo.

---

### Edge Cases

- Um lançamento PJ no mesmo dia de um salário PF não afeta o ciclo PF.
- Excluir o único salário de um `clt_prestador` continua sendo recusado se deixar lançamentos
  PF fora de ciclo; lançamentos PJ não contam nessa verificação.
- Trocar de `prestador` para `clt_prestador` verifica a cobertura por salário só dos
  lançamentos PF, inclusive o lado PF das retiradas.
- Mudar a carteira de um lançamento existente (PF ↔ PJ) segue todas as regras da carteira de
  destino; lados de retirada não podem mudar de carteira.
- Lançamentos PJ seguem o filtro do saldo de sempre: só realizados e com `conta no saldo`.
- O limite por categoria, a projeção do ciclo e o calendário mostram só a carteira aberta.
- Categorias são compartilhadas entre as carteiras; as duas categorias de sistema novas são
  criadas quando a pessoa liga a PJ e não podem ser renomeadas nem desativadas.
- O administrador passa a ver, no detalhe da conta, a contagem de retiradas e os eventos de
  retirada, sem valores.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Usuários `prestador` e `clt_prestador` MUST poder ligar e desligar a carteira PJ
  no perfil; usuários `clt` MUST ter a ação recusada.
- **FR-002**: Todo lançamento e toda recorrência MUST pertencer a uma carteira (PF ou PJ). Sem
  a carteira informada, vale PF.
- **FR-003**: Lançar ou criar recorrência na PJ MUST ser recusado se a PJ não estiver ligada.
- **FR-004**: O ciclo da PJ MUST ser sempre o mês do calendário, sem exigir salário. O ciclo da
  PF MUST seguir as regras atuais do tipo de renda.
- **FR-005**: A verificação de cobertura por salário (primeiro salário, exclusão ou mudança de
  data de salário, troca de tipo de renda) MUST considerar só lançamentos PF.
- **FR-006**: Lançar "Salário" na PJ MUST ser recusado.
- **FR-007**: Ciclo, lista de lançamentos, saldo, gasto por categoria, limite por categoria,
  projeção e calendário MUST mostrar só a carteira pedida, PF por padrão. Nenhuma tela MUST
  somar as duas carteiras.
- **FR-008**: A retirada MUST gerar, numa única operação, uma saída realizada na PJ ("Retirada
  para PF") e uma entrada realizada na PF ("Pró-labore e lucros"), de mesmo valor e data.
- **FR-009**: Editar ou excluir a retirada MUST alterar os dois lados juntos; editar ou excluir
  um lado pelo lançamento MUST ser recusado.
- **FR-010**: A retirada MUST exigir valor maior que zero, data até hoje e PJ ligada, e o lado
  PF MUST respeitar as regras de ciclo da PF.
- **FR-011**: Recorrências da PJ MUST gerar um previsto por mês do calendário, sem duplicar, e
  nunca na PF.
- **FR-012**: Os lembretes MUST juntar as duas carteiras e marcar cada item com PF ou PJ.
- **FR-013**: Desligar a PJ ou trocar para `clt` MUST ser recusado enquanto houver lançamento,
  recorrência ou retirada na PJ.
- **FR-014**: Ao ligar a PJ, as categorias de sistema "Retirada para PF" (saída) e "Pró-labore e
  lucros" (entrada) MUST existir para o usuário, protegidas contra renomear e desativar.
- **FR-015**: Dívidas, cartelas, serviços e importação de extrato MUST continuar só na PF nesta
  fase.
- **FR-016**: O sistema MUST NOT calcular impostos.
- **FR-017**: Criar, editar e excluir uma retirada MUST gerar os eventos de uso
  correspondentes, e as retiradas MUST entrar nas contagens do detalhe da conta do
  administrador, sem valores.

### Key Entities

- **Carteira**: a quem o dinheiro pertence: PF (a pessoa) ou PJ (a empresa da pessoa). É um
  atributo de lançamentos e recorrências, não uma conta bancária.
- **Retirada**: dinheiro que sai da PJ para a PF (pró-labore ou distribuição de lucros). Tem
  valor e data e é dona dos dois lançamentos que a representam.
- **Usuário** (já existe): ganha a informação de que tem a carteira PJ ligada.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Com os dados do exemplo de referência, o sistema mostra exatamente R$ 2.625,00 na
  PJ e R$ 2.300,00 na PF em outubro.
- **SC-002**: Em 100% das retiradas, os dois lados têm o mesmo valor e a mesma data depois de
  qualquer criação, edição ou exclusão.
- **SC-003**: Nenhuma tela de ciclo, saldo, gasto, limite, projeção ou calendário mostra um
  lançamento da carteira que não está aberta (verificado em todas as rotas de leitura).
- **SC-004**: Quem não liga a PJ não vê nenhuma diferença no uso atual: todos os testes
  existentes continuam passando sem alteração de comportamento.
- **SC-005**: Uma pessoa registra uma retirada em menos de 30 segundos, com uma única ação.

## Assumptions

- "PJ" é a empresa da própria pessoa (MEI ou ME). Caixa de empresa com vários usuários está
  fora do escopo.
- Categorias são compartilhadas entre as carteiras. Separar categorias por carteira fica para
  depois, se o uso pedir.
- A carteira PJ fica disponível para `clt` só depois da troca para `clt_prestador`.
- A retirada é sempre realizada; não existe retirada prevista nesta fase.
- O resumo diário por push continua uma única notificação para as duas carteiras.
- Visão consolidada, serviços na PJ e importação por carteira ficam para a fase 2.
- Escopo backend e frontend.
