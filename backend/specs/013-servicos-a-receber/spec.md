# Feature Specification: Serviços a Receber

**Feature Branch**: `013-servicos-a-receber`

**Created**: 2026-09-30

**Status**: Draft

**Input**: Pedido explícito do usuário em 2026-09-30: quem presta serviço precisa acompanhar o
que os clientes ainda vão pagar. Constituição 4.3.0 (Princípio VI, "Serviço a receber"); depende
da feature 012 (tipo de renda).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Registrar um serviço a receber (Priority: P1)

Presto um serviço e anoto quem vai me pagar, quanto e quando espero receber. O valor passa a
aparecer como uma entrada prevista no ciclo da data prevista.

**Why this priority**: é o registro básico; sem ele não há o que acompanhar nem receber.

**Independent Test**: como prestador, registrar um serviço de R$ 800,00 para "Loja da Maria"
previsto para 20/10 e ver a entrada prevista nos lançamentos do ciclo.

**Acceptance Scenarios**:

1. **Given** sou prestador, **When** registro um serviço para "Loja da Maria", R$ 800,00,
   previsto para 20/10, na categoria "Renda extra", **Then** o serviço aparece como "a receber"
   e existe uma entrada prevista de R$ 800,00 em 20/10 em "Renda extra", ligada ao serviço.
2. **Given** sou prestador, **When** registro um serviço sem cliente, com valor zero ou negativo,
   ou com fração de centavo, **Then** o registro é recusado e o campo é apontado.
3. **Given** sou prestador, **When** escolho uma categoria de saída, inativa ou "Salário",
   **Then** o registro é recusado explicando que precisa ser uma categoria de entrada.
4. **Given** sou prestador, **When** registro um serviço com data prevista no passado, **Then** ele
   é aceito e aparece como "atrasado".
5. **Given** sou CLT (só salário), **When** tento acessar ou registrar serviços, **Then** o acesso é
   recusado explicando que serviços são para quem presta serviço.
6. **Given** sou "CLT e prestador" sem salário lançado, **When** registro um serviço, **Then** o
   registro é recusado pedindo o salário, como qualquer lançamento.

---

### User Story 2 - Marcar como recebido (Priority: P1)

O cliente pagou. Marco o serviço como recebido, informando a data em que o dinheiro entrou e, se
for diferente, quanto recebi. A entrada passa a contar no saldo do ciclo.

**Why this priority**: é o momento em que o dinheiro entra de fato; sem isso o serviço nunca
sai de "a receber".

**Independent Test**: registrar um serviço de R$ 800,00, receber em 18/10 e ver o saldo do ciclo
subir R$ 800,00.

**Acceptance Scenarios**:

1. **Given** um serviço de R$ 800,00 a receber, **When** marco como recebido em 18/10 sem
   informar valor, **Then** o serviço fica "recebido" e a entrada vira realizada, em 18/10, de
   R$ 800,00, contando no saldo.
2. **Given** um serviço de R$ 800,00, **When** marco como recebido informando R$ 750,00, **Then**
   a entrada realizada é de R$ 750,00 e o serviço continua registrando R$ 800,00 como combinado.
3. **Given** um serviço a receber, **When** tento marcar como recebido com data futura, **Then** a
   operação é recusada.
4. **Given** um serviço já recebido, **When** tento receber de novo, **Then** a operação é
   recusada.
5. **Given** um serviço recebido por engano, **When** desfaço o recebimento, **Then** a entrada
   volta a prevista, na data prevista e com o valor do serviço, e o serviço volta a "a receber"
   ou "atrasado".
6. **Given** um serviço ainda não recebido, **When** tento desfazer o recebimento, **Then** a
   operação é recusada.

---

### User Story 3 - Ver o que tenho a receber (Priority: P1)

Vejo a lista dos meus serviços, podendo filtrar pelos a receber, atrasados ou recebidos, para
saber quem ainda me deve.

**Why this priority**: é a pergunta central de quem presta serviço: "quem ainda não me pagou?".

**Independent Test**: com serviços nas três situações, listar todos e filtrar por "atrasado".

**Acceptance Scenarios**:

1. **Given** três serviços (um a receber, um atrasado, um recebido), **When** listo sem filtro,
   **Then** vejo os três, ordenados pela data prevista.
2. **Given** os mesmos serviços, **When** filtro por "atrasado", **Then** vejo só o atrasado.
3. **Given** um serviço previsto para hoje, **When** listo, **Then** ele está "a receber" (só fica
   atrasado a partir de amanhã).
4. **Given** um serviço recebido, **When** o consulto, **Then** vejo também a data e o valor
   recebidos.
5. **Given** outra pessoa com serviços, **When** listo os meus, **Then** não vejo os dela; ao
   tentar abrir um serviço dela, ele não é encontrado.

---

### User Story 4 - Corrigir ou excluir um serviço (Priority: P2)

Errei o valor ou a data, ou o serviço foi cancelado. Enquanto não recebi, corrijo ou excluo o
serviço, e a entrada prevista acompanha.

**Why this priority**: correções são comuns, mas o registro e o recebimento já entregam valor.

**Independent Test**: editar o valor de um serviço a receber e conferir a entrada prevista;
excluir e ver a entrada sumir.

**Acceptance Scenarios**:

1. **Given** um serviço a receber, **When** mudo o valor para R$ 900,00 e a data prevista para
   25/10, **Then** a entrada prevista passa a ser de R$ 900,00 em 25/10.
2. **Given** um serviço a receber, **When** mudo o cliente, a descrição ou a categoria, **Then** a
   entrada prevista acompanha a categoria e a descrição.
3. **Given** um serviço a receber, **When** o excluo, **Then** o serviço e a entrada prevista
   somem.
4. **Given** um serviço recebido, **When** tento editar ou excluir, **Then** a operação é recusada,
   pedindo para desfazer o recebimento antes.
5. **Given** a entrada ligada a um serviço, **When** tento mudar valor, situação, categoria ou
   data dela, ou excluí-la, pela tela de lançamentos, **Then** a mudança é recusada, pedindo para
   fazê-la pelo serviço. A descrição da entrada pode ser mudada.

---

### User Story 5 - Deixar de prestar serviço (Priority: P3)

Parei de prestar serviço e quero voltar a ser só CLT. Só consigo trocar quando não há serviços
pendentes.

**Why this priority**: troca rara; protege contra serviços pendentes esquecidos.

**Independent Test**: com um serviço a receber, tentar trocar para CLT e ver a recusa; excluir o
serviço e trocar.

**Acceptance Scenarios**:

1. **Given** sou "CLT e prestador" com um serviço a receber, **When** tento mudar para CLT,
   **Then** a troca é recusada, explicando que há serviços pendentes.
2. **Given** sou "CLT e prestador" só com serviços recebidos, **When** mudo para CLT, **Then** a
   troca é aceita e as entradas desses serviços continuam no saldo como lançamentos normais, sem
   trava.
3. **Given** sou prestador com serviços a receber e todos os lançamentos cobertos por salário,
   **When** mudo para "CLT e prestador", **Then** a troca é aceita e os serviços continuam
   visíveis.

---

### Edge Cases

- Valor recebido diferente do combinado: o saldo usa o valor recebido; o serviço guarda o
  combinado. Desfazer o recebimento volta a entrada ao valor combinado.
- Recebimento antes da data prevista é aceito (cliente pagou adiantado).
- Para "CLT e prestador", a data prevista e a data do recebimento precisam cair num ciclo de
  salário, como qualquer lançamento.
- Categoria desativada depois do registro: o serviço continua funcionando, mas editar exige
  escolher uma categoria ativa se a categoria for trocada.
- A entrada prevista de um serviço não conta no saldo nem no gasto por categoria até ser recebida
  (mesmo filtro do saldo).
- A descrição da entrada gerada é o cliente, seguido da descrição do serviço quando houver.
- Cliente com mais de 120 caracteres ou descrição com mais de 200 são recusados; texto só com
  espaços conta como vazio.
- Um usuário nunca vê, recebe, edita ou exclui serviços de outro (não encontrado).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Usuários "prestador" e "clt_prestador" MUST poder registrar serviços com cliente
  (obrigatório, até 120 caracteres), descrição (opcional, até 200), valor (centavos inteiros,
  maior que zero), data prevista e categoria (ativa, de entrada, diferente de "Salário").
- **FR-002**: Usuários "clt" MUST ter todo acesso a serviços recusado, com uma mensagem clara.
- **FR-003**: Registrar um serviço MUST criar, na mesma operação, uma entrada prevista com o
  valor, a categoria e a data prevista do serviço, ligada a ele.
- **FR-004**: A situação do serviço MUST ser derivada: "recebido" se a entrada estiver
  realizada; senão "atrasado" se a data prevista for anterior a hoje; senão "a_receber". Ela
  MUST NOT ser guardada.
- **FR-005**: Receber MUST exigir a data do recebimento (não futura) e aceitar um valor recebido
  opcional (padrão: o valor do serviço); a entrada vira realizada com essa data e valor.
- **FR-006**: Desfazer o recebimento MUST devolver a entrada a prevista, na data prevista e com o
  valor do serviço.
- **FR-007**: Editar e excluir um serviço MUST ser possível só enquanto não recebido; editar
  MUST atualizar a entrada prevista; excluir MUST remover o serviço e a entrada.
- **FR-008**: A listagem MUST aceitar filtro opcional por situação e ordenar por data prevista
  (e, no empate, pela ordem de registro).
- **FR-009**: Um serviço recebido MUST mostrar a data e o valor recebidos.
- **FR-010**: A entrada ligada a um serviço MUST NOT ter valor, situação, categoria ou data
  alterados, nem ser excluída, pela gestão de lançamentos, enquanto o usuário tiver acesso a
  serviços. Para "clt", essas entradas se comportam como lançamentos normais.
- **FR-011**: Todo lançamento MUST indicar a qual serviço está ligado, quando estiver.
- **FR-012**: Para "clt_prestador", registrar, editar, receber e desfazer MUST seguir as regras de
  cobertura do ciclo pelo salário.
- **FR-013**: A troca para "clt" MUST ser recusada enquanto houver serviço não recebido.
- **FR-014**: Serviços MUST ser visíveis e alteráveis só pelo próprio usuário; serviço de outro
  MUST ser tratado como não encontrado.

### Key Entities

- **Serviço**: cliente, descrição, valor combinado, data prevista, categoria; pertence a um
  usuário e está ligado a exatamente uma entrada (lançamento).
- **Situação do serviço** (derivada): a_receber, atrasado ou recebido.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Registrar um serviço leva uma única ação e ele já aparece como entrada prevista no
  ciclo.
- **SC-002**: Em 100% dos casos, o saldo do ciclo muda exatamente pelo valor recebido no
  recebimento, e volta ao anterior ao desfazer.
- **SC-003**: A situação bate com a regra em 100% dos casos de fronteira (data prevista ontem,
  hoje e amanhã).
- **SC-004**: Nenhuma entrada de serviço pode ficar em desacordo com o serviço: não existe
  caminho para alterar, pelos lançamentos, o que o serviço controla.
- **SC-005**: Nenhum usuário CLT consegue ver ou criar serviços.

## Assumptions

- Pedido explícito do usuário em 2026-09-30; constituição 4.3.0.
- Depende da feature 012 (tipo de renda).
- Um serviço tem um único pagamento; parcelamento de serviço fica fora (o usuário pode registrar
  vários serviços).
- Sem cadastro de clientes: o cliente é um texto livre no serviço.
- Sem emissão de nota, cobrança ou lembrete automático.
- Escopo: só backend (API). A tela de serviços no frontend fica para depois.
