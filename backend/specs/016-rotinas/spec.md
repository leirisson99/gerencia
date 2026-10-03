# Feature Specification: Rotinas de Gastos e Entradas

**Feature Branch**: `016-rotinas`

**Created**: 2026-10-02

**Status**: Draft

**Input**: Pedido explícito do usuário em 2026-10-02: entender a rotina dos próprios gastos e
entradas com filtros, como base para um agente de insights futuro (017) que só vai consultar
estas rotinas. Decisões do usuário: quatro rotinas (dia da semana, ritmo do ciclo, frequentes
sem recorrência, comparação com ciclos anteriores); rotinas 100% determinísticas antes do agente.
Constituição 5.3.0 (Princípio VI, "Rotinas").

## User Scenarios & Testing *(mandatory)*

Em todas as rotinas valem as mesmas regras do saldo: só contam lançamentos realizados que contam
no saldo. Previstos, depósitos de cartela e compras pagas no cartão (que entram só como fatura)
ficam de fora. Todo valor é exibido em reais e calculado em centavos exatos.

### User Story 1 - Ver em que dias da semana o dinheiro sai (Priority: P1)

Abro a página Rotinas e vejo, para o ciclo atual, quanto saiu em cada dia da semana, de segunda a
domingo, com a participação de cada dia no total e quantos lançamentos houve.

**Why this priority**: é a rotina mais imediata de entender ("gasto mais no fim de semana") e
também abre a página com os filtros, que as outras rotinas reaproveitam.

**Independent Test**: com R$ 100,00 de saídas numa sexta, R$ 300,00 num sábado e R$ 100,00 numa
segunda do ciclo atual, abrir Rotinas e ver sábado com 60%, sexta e segunda com 20% cada e os
outros dias com zero.

**Acceptance Scenarios**:

1. **Given** as saídas acima, **When** abro Rotinas, **Then** vejo os 7 dias na ordem segunda a
   domingo, cada um com total, quantidade e participação, e o sábado destacado como o dia de
   maior gasto.
2. **Given** uma saída prevista num domingo, **When** abro Rotinas, **Then** ela não conta.
3. **Given** um depósito de cartela numa quarta, **When** abro Rotinas, **Then** ele não conta.
4. **Given** escolho o tipo "entrada", **When** a página atualiza, **Then** vejo a mesma rotina
   calculada só com as entradas.
5. **Given** escolho a categoria "Mercado", **When** a página atualiza, **Then** a rotina considera
   só os lançamentos de Mercado.
6. **Given** o ciclo não tem nenhum lançamento do tipo escolhido, **When** abro Rotinas, **Then**
   vejo "dados insuficientes" em vez de uma distribuição zerada.

---

### User Story 2 - Ver o ritmo do ciclo (Priority: P1)

Vejo quanto do total do ciclo saiu na 1ª semana (dias 1 a 7 do ciclo), na 2ª semana (dias 8 a 14)
e no restante (do dia 15 em diante), com a participação de cada fase e o acumulado.

**Why this priority**: responde se o dinheiro "acaba cedo" depois do salário, o que é a dúvida
central de quem vive de ciclo em ciclo.

**Independent Test**: num ciclo que começa em 05/09 (salário), com R$ 600,00 de saídas entre 05/09
e 11/09, R$ 200,00 entre 12/09 e 18/09 e R$ 200,00 depois, ver 60%, 20% e 20%, com acumulado de
60%, 80% e 100%.

**Acceptance Scenarios**:

1. **Given** o cenário acima, **When** abro Rotinas, **Then** vejo as três fases com total,
   participação e acumulado.
2. **Given** sou prestador, **When** abro Rotinas em setembro, **Then** as fases contam a partir
   de 01/09 (dias 1 a 7, 8 a 14, 15 até o fim do mês).
3. **Given** o ciclo atual está no 10º dia, **When** abro Rotinas, **Then** a fase "restante"
   aparece como ainda não iniciada, sem valor, em vez de zero.
4. **Given** o ciclo não tem lançamentos do tipo escolhido, **When** abro Rotinas, **Then** vejo
   "dados insuficientes".

---

### User Story 3 - Descobrir gastos frequentes que não são fixos (Priority: P2)

Vejo as categorias que aparecem muitas vezes no ciclo (4 ou mais lançamentos) sem terem vindo de
uma recorrência, com quantidade e total, comparadas com o total dos meus fixos (recorrências) no
mesmo ciclo.

**Why this priority**: revela os "fixos invisíveis" (delivery, transporte por aplicativo), que
pesam como uma conta fixa sem estarem cadastrados como uma.

**Independent Test**: com 5 lançamentos manuais de Delivery somando R$ 250,00, 2 de Farmácia e
uma recorrência de Internet de R$ 100,00 realizada no ciclo, ver só Delivery na lista, com 5
lançamentos, R$ 250,00 e a indicação de que é mais que o total dos fixos (R$ 100,00).

**Acceptance Scenarios**:

1. **Given** o cenário acima, **When** abro Rotinas, **Then** Delivery aparece com quantidade e
   total, e Farmácia não aparece (menos de 4 lançamentos).
2. **Given** 4 lançamentos de Aluguel no ciclo, todos gerados por recorrência, **When** abro
   Rotinas, **Then** Aluguel não aparece como frequente e entra no total dos fixos.
3. **Given** duas categorias frequentes, **When** abro Rotinas, **Then** elas aparecem da maior
   para a menor pelo total.
4. **Given** nenhuma categoria chega a 4 lançamentos, **When** abro Rotinas, **Then** vejo que
   não há gastos frequentes fora dos fixos neste ciclo.

---

### User Story 4 - Comparar o ciclo com os anteriores (Priority: P2)

Vejo, para cada categoria, o total do ciclo escolhido contra a média dos até 3 ciclos anteriores,
com a variação em porcentagem. Variações de 20% ou mais, para cima ou para baixo, aparecem em
destaque. No ciclo em andamento, a comparação é justa: os ciclos anteriores contam só até o mesmo
dia do ciclo.

**Why this priority**: mostra o que mudou na rotina, mas só tem valor depois de alguns ciclos de
uso.

**Independent Test**: com Mercado em R$ 600,00, R$ 400,00 e R$ 500,00 nos três ciclos anteriores
(média R$ 500,00) e R$ 650,00 no ciclo escolhido (fechado), ver Mercado com +30% em destaque.

**Acceptance Scenarios**:

1. **Given** o cenário acima, **When** abro Rotinas no ciclo escolhido, **Then** Mercado aparece
   com total, média, variação de +30% e destaque.
2. **Given** o ciclo atual está no 10º dia, **When** abro Rotinas, **Then** cada ciclo anterior
   entra na média só com os lançamentos dos seus 10 primeiros dias.
3. **Given** só existe 1 ciclo anterior, **When** abro Rotinas, **Then** a média usa só esse ciclo
   e a página diz que a comparação usa 1 ciclo.
4. **Given** não existe ciclo anterior, **When** abro Rotinas, **Then** vejo "dados insuficientes"
   na comparação.
5. **Given** uma categoria que não apareceu nos ciclos anteriores, **When** abro Rotinas, **Then**
   ela aparece como nova, sem porcentagem.
6. **Given** uma categoria que existia nos anteriores e não teve lançamento no ciclo escolhido,
   **When** abro Rotinas, **Then** ela aparece com total zero e variação de −100%.
7. **Given** Transporte variou só +10%, **When** abro Rotinas, **Then** ela aparece sem destaque.

---

### User Story 5 - Ver rotinas de um ciclo anterior (Priority: P3)

Navego para um ciclo anterior e vejo as quatro rotinas calculadas para ele.

**Why this priority**: útil para revisar, mas o uso principal é o ciclo atual.

**Independent Test**: voltar um ciclo e ver as rotinas daquele período; a comparação usa os até 3
ciclos anteriores a ele, sem proporcionalidade (ciclo fechado).

**Acceptance Scenarios**:

1. **Given** estou no ciclo atual, **When** volto para o anterior, **Then** as quatro rotinas são
   recalculadas para ele, mantendo o tipo e a categoria escolhidos.
2. **Given** escolho uma data em que ainda não havia ciclo, **When** peço as rotinas, **Then**
   recebo a mesma resposta de "sem ciclo" das outras telas.

### Edge Cases

- **Usuário `clt` sem salário lançado**: não há ciclo; a página orienta a lançar o salário, como o
  dashboard.
- **Prestador novo**: meses do calendário anteriores ao mês do primeiro lançamento não contam como
  ciclos anteriores; se não houver nenhum, a comparação diz "dados insuficientes".
- **Categoria de outro usuário** no filtro: resposta "não encontrado", como nas outras telas.
- **Categoria de tipo diferente do tipo escolhido** (ex.: "Salário" com tipo saída): o pedido é
  recusado com mensagem clara.
- **Categoria inativa**: seus lançamentos continuam contando; a rotina é sobre o que aconteceu.
- **Fatura do cartão**: aparece como a categoria "Cartão de crédito", no dia em que a fatura foi
  paga; a página avisa que compras no cartão não aparecem uma a uma.
- **Porcentagens arredondadas**: a soma das participações pode dar 99% ou 101%; os totais em
  centavos sempre somam exatamente o total do ciclo.
- **Ciclo de 1 dia** (dois salários em dias seguidos): só a 1ª semana tem dados; as outras fases
  aparecem como não alcançadas.
- **Ciclo `clt` fechado com menos de 15 dias**: a fase "restante" aparece como não alcançada.
- **Salário (entrada)**: conta normalmente nas rotinas de entrada.

## Requirements *(mandatory)*

### Functional Requirements

**Base comum**

- **FR-001**: O sistema MUST calcular as rotinas só com lançamentos do usuário autenticado que
  estejam realizados e contem no saldo, do tipo escolhido (entrada ou saída; padrão: saída).
- **FR-002**: O usuário MUST poder escolher o ciclo (o atual por padrão, ou o ciclo que contém
  uma data informada), o tipo e, opcionalmente, uma categoria; o filtro de categoria vale para as
  quatro rotinas.
- **FR-003**: Filtrar por categoria de outro usuário MUST resultar em "não encontrado"; filtrar
  por categoria de tipo diferente do escolhido MUST ser recusado com mensagem clara.
- **FR-004**: Sem ciclo para a data (usuário `clt`/`clt_prestador` sem salário, ou data anterior
  ao primeiro ciclo), o sistema MUST responder como as demais consultas de ciclo ("sem ciclo").
- **FR-005**: As rotinas MUST ser derivadas a cada consulta, MUST NOT ser armazenadas e a consulta
  MUST NOT gravar nada.
- **FR-006**: Toda rotina sem base para um padrão MUST indicar "dados insuficientes" em vez de
  exibir valores zerados ou inferidos.
- **FR-007**: Valores MUST ser centavos inteiros; participações e variações MUST ser porcentagens
  inteiras arredondadas, e a soma dos totais de cada rotina MUST ser igual ao total considerado.
- **FR-008**: A página MUST avisar que compras no cartão de crédito aparecem só como a fatura.

**Rotina 1: dia da semana**

- **FR-010**: O sistema MUST mostrar os 7 dias, de segunda a domingo, cada um com total,
  quantidade de lançamentos e participação no total do ciclo, e indicar o dia de maior total.
- **FR-011**: Sem nenhum lançamento considerado, a rotina MUST indicar "dados insuficientes".

**Rotina 2: ritmo do ciclo**

- **FR-020**: O sistema MUST dividir o ciclo em três fases contadas a partir do início do ciclo:
  1ª semana (dias 1 a 7), 2ª semana (dias 8 a 14) e restante (dia 15 até o fim), mostrando total,
  participação e participação acumulada de cada fase.
- **FR-021**: O início do ciclo MUST ser o mesmo das demais telas: a data do salário para `clt` e
  `clt_prestador` e o dia 1 do mês para `prestador`.
- **FR-022**: Fases que o ciclo ainda não alcançou (ciclo aberto) ou não tem (ciclo fechado
  curto) MUST aparecer como não alcançadas, sem valor.
- **FR-023**: Sem nenhum lançamento considerado, a rotina MUST indicar "dados insuficientes".

**Rotina 3: frequentes sem recorrência**

- **FR-030**: O sistema MUST listar as categorias com 4 ou mais lançamentos considerados no ciclo
  que não foram gerados por uma recorrência, com quantidade e total, da maior para a menor pelo
  total.
- **FR-031**: O sistema MUST mostrar o total, no mesmo ciclo e tipo, dos lançamentos gerados por
  recorrências, para comparação com cada categoria frequente.
- **FR-032**: Sem categoria frequente, a rotina MUST dizer que não há gastos frequentes fora dos
  fixos no ciclo.

**Rotina 4: comparação com ciclos anteriores**

- **FR-040**: O sistema MUST comparar, para cada categoria presente no ciclo escolhido ou em algum
  dos ciclos anteriores considerados, o total do ciclo escolhido com a média dos até 3 ciclos
  imediatamente anteriores.
- **FR-041**: A média MUST dividir a soma pelo número de ciclos anteriores considerados, incluindo
  os ciclos em que a categoria teve total zero.
- **FR-042**: Se o ciclo escolhido estiver aberto e estiver no dia N, cada ciclo anterior MUST
  contar só os lançamentos dos seus N primeiros dias.
- **FR-043**: A variação MUST ser (total − média) ÷ média, em porcentagem inteira; categorias com
  média zero MUST aparecer como novas, sem porcentagem; variações de 20% ou mais, em módulo,
  MUST ser destacadas.
- **FR-044**: Só contam como ciclos anteriores os que começam no ciclo do primeiro lançamento do
  usuário ou depois dele; sem nenhum ciclo anterior, a rotina MUST indicar "dados insuficientes".
- **FR-045**: A rotina MUST informar quantos ciclos anteriores entraram na média.
- **FR-046**: As categorias MUST ser ordenadas pelo tamanho da variação em reais, da maior para a
  menor.

**Interface**

- **FR-050**: A página Rotinas MUST estar no menu da área logada e funcionar no celular e no
  computador, ocupando a largura toda.
- **FR-051**: A página MUST permitir navegar entre ciclos (anterior e próximo), trocar o tipo e
  escolher uma categoria do tipo escolhido, mantendo os filtros ao navegar.

### Key Entities *(include if feature involves data)*

Nenhuma entidade nova é armazenada. As rotinas são visões derivadas de:

- **Lançamento**: data, valor, tipo, categoria, status, se conta no saldo e se veio de recorrência.
- **Ciclo**: início e fim derivados (salário ou mês do calendário), como nas demais telas.
- **Categoria**: nome e tipo, para agrupar e filtrar.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em 100% dos casos de teste, a soma dos totais de cada rotina é igual, ao centavo, ao
  total de lançamentos considerados no ciclo com os mesmos filtros.
- **SC-002**: Em 100% dos casos de teste, previstos, depósitos de cartela e lançamentos fora do
  saldo não aparecem em nenhuma rotina.
- **SC-003**: Um usuário com pelo menos 2 ciclos de dados identifica, em menos de 1 minuto na
  página, o dia da semana em que mais gasta, a fase do ciclo em que mais gasta e a categoria que
  mais cresceu.
- **SC-004**: A página Rotinas exibe as quatro rotinas em até 2 segundos para um usuário com 12
  ciclos e 1.000 lançamentos.
- **SC-005**: Nenhuma consulta de rotinas expõe dados de outro usuário (verificado por teste).

## Assumptions

- As fases do ritmo (7, 7 e o restante) e os limites (4 lançamentos para "frequente", 20% para
  destaque, até 3 ciclos para a média) são fixos nesta versão, sem configuração pelo usuário.
- "Veio de recorrência" é o lançamento gerado por uma recorrência cadastrada; parcelas de dívida e
  entradas de serviço contam como lançamentos comuns na rotina de frequentes.
- O tipo padrão é saída, porque o problema central do produto é saber para onde o dinheiro vai.
- A página reaproveita a navegação de ciclos já existente nas outras telas.
- O agente de insights (feature 017) está fora do escopo; esta feature só garante que as rotinas
  estejam disponíveis para consulta pela própria API.
- Lançamentos não guardam horário, então não há rotina por hora do dia.
