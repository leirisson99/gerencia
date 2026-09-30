# Feature Specification: Tipo de Renda e Ciclo Mensal do Prestador

**Feature Branch**: `012-prestador-ciclo-mensal`

**Created**: 2026-09-30

**Status**: Draft

**Input**: Pedido explícito do usuário em 2026-09-30: amigos que prestam serviço também vão
usar o sistema, e hoje nada pode ser lançado sem um salário. Constituição 4.3.0, Princípio II
("Ciclo Derivado do Tipo de Renda").

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Informar como recebo (Priority: P1)

Ao me cadastrar, digo se sou CLT (só salário), prestador de serviço (só presto serviço) ou os
dois. Se eu não disser nada, sou CLT, como sempre foi. Vejo meu tipo de renda no meu perfil e
posso mudá-lo depois.

**Why this priority**: o tipo de renda decide como o ciclo é calculado; sem ele, nada mais desta
feature funciona.

**Independent Test**: cadastrar três contas, uma de cada tipo, e uma sem informar; conferir o tipo
de cada uma no perfil.

**Acceptance Scenarios**:

1. **Given** o cadastro, **When** me cadastro informando "prestador", **Then** meu perfil mostra
   o tipo de renda "prestador".
2. **Given** o cadastro, **When** me cadastro sem informar o tipo de renda, **Then** meu perfil
   mostra "clt".
3. **Given** o cadastro, **When** informo um tipo de renda que não existe, **Then** o cadastro é
   recusado e o campo é apontado como inválido.
4. **Given** uma conta criada antes desta feature, **When** consulto o perfil, **Then** o tipo de
   renda é "clt" e tudo funciona como antes.
5. **Given** minha conta "clt", **When** mudo para "clt_prestador" no perfil, **Then** a mudança é
   aceita e meus ciclos continuam os mesmos.

---

### User Story 2 - Prestador controla o mês sem lançar salário (Priority: P1)

Sou prestador de serviço. Recebo de vários clientes em datas diferentes e não tenho salário.
Lanço entradas e gastos desde o primeiro dia, e o sistema organiza tudo por mês: o ciclo atual é
o mês de hoje, e o saldo e o gasto por categoria são os do mês.

**Why this priority**: é o problema que motivou a feature: hoje o prestador fica travado sem um
salário para abrir o ciclo.

**Independent Test**: com uma conta "prestador" nova, lançar um gasto e uma entrada sem nenhum
salário e consultar o ciclo atual e o resumo.

**Acceptance Scenarios**:

1. **Given** uma conta "prestador" sem lançamentos, **When** lanço um gasto de R$ 50,00 em
   Alimentação com data de hoje, **Then** o lançamento é aceito (não há pedido de salário).
2. **Given** hoje é 15/10/2026 e sou "prestador", **When** consulto o ciclo atual, **Then** ele vai
   de 01/10/2026 a 31/10/2026 e está aberto.
3. **Given** sou "prestador" e não tenho lançamentos, **When** consulto o ciclo atual, **Then**
   recebo o mês de hoje (nunca "sem ciclo").
4. **Given** sou "prestador" e lancei R$ 2.000,00 de entrada e R$ 500,00 de gasto realizados em
   outubro, **When** peço o resumo de outubro, **Then** o saldo é R$ 1.500,00.
5. **Given** sou "prestador", **When** consulto o ciclo de 10/02/2028, **Then** ele vai de
   01/02/2028 a 29/02/2028 (ano bissexto).
6. **Given** sou "prestador" e lanço uma entrada em "Salário", **When** consulto o ciclo atual,
   **Then** o ciclo continua sendo o mês: o lançamento em "Salário" não abre ciclo e aparece como
   uma entrada comum.
7. **Given** sou "prestador", **When** lanço uma entrada prevista em "Salário" com data futura,
   **Then** o lançamento é aceito (para o prestador, "Salário" não tem as regras de salário).
8. **Given** sou "prestador" e tenho lançamentos desde agosto, **When** consulto o ciclo de
   outubro (mês atual), **Then** o anterior é 01/09/2026 e não há próximo; **When** consulto
   agosto, **Then** não há anterior, porque não tenho lançamentos antes de agosto.

---

### User Story 3 - Fixos e limites valem no mês do prestador (Priority: P2)

Como prestador, meus gastos fixos (aluguel, internet) aparecem como previstos em cada mês, e o
limite por categoria é medido dentro do mês.

**Why this priority**: sem isso o prestador perde recursos que o CLT já tem, mas o controle
básico do mês (história 2) já entrega valor.

**Independent Test**: com uma conta "prestador", cadastrar o aluguel como recorrência no dia 10 e
conferir o previsto no mês atual; definir limite em Lazer e lançar gastos no mês.

**Acceptance Scenarios**:

1. **Given** sou "prestador" e cadastro o aluguel de R$ 1.200,00 no dia 10, **When** consulto os
   lançamentos do mês atual, **Then** existe um previsto de R$ 1.200,00 no dia 10 deste mês.
2. **Given** tenho o aluguel como recorrência e chega um mês novo, **When** consulto o ciclo atual
   ou o resumo pela primeira vez no mês, **Then** o previsto do aluguel do novo mês aparece.
3. **Given** o previsto do aluguel já existe no mês, **When** consulto o ciclo atual várias vezes,
   **Then** continua existindo um único previsto do aluguel no mês.
4. **Given** uma recorrência no dia 31 e o mês de fevereiro, **When** o previsto é gerado, **Then**
   ele cai no último dia de fevereiro.
5. **Given** sou "prestador" com limite de R$ 300,00 em Lazer e R$ 250,00 gastos em setembro,
   **When** lanço R$ 100,00 em Lazer no dia 01/10, **Then** não há aviso: o gasto de setembro não
   conta em outubro.

---

### User Story 4 - Trocar o tipo de renda sem perder dados (Priority: P2)

Minha situação muda (arrumei um emprego, virei autônomo). Troco o tipo de renda no perfil, e os
ciclos passam a seguir a nova regra, sem perder nenhum lançamento.

**Why this priority**: a troca é rara, mas precisa ser segura: não pode deixar lançamentos fora
de ciclo.

**Independent Test**: trocar uma conta "clt" com salário para "prestador" e de volta; tentar
trocar um "prestador" sem salário para "clt" e ver a recusa.

**Acceptance Scenarios**:

1. **Given** sou "clt" com salários lançados, **When** mudo para "prestador", **Then** a mudança é
   aceita e o ciclo atual passa a ser o mês de hoje; os lançamentos continuam os mesmos.
2. **Given** sou "prestador" sem nenhum salário e com lançamentos, **When** tento mudar para "clt"
   ou "clt_prestador", **Then** a mudança é recusada, explicando que é preciso lançar o salário
   antes.
3. **Given** sou "prestador" com um salário realizado em 05/09 e um gasto em 02/09, **When** tento
   mudar para "clt", **Then** a mudança é recusada, pois o gasto ficaria antes do primeiro ciclo.
4. **Given** sou "prestador" com um salário realizado em 05/09 e todos os outros lançamentos a
   partir de 05/09, **When** mudo para "clt", **Then** a mudança é aceita e os ciclos passam a
   começar nas datas de salário.
5. **Given** sou "prestador" sem nenhum lançamento, **When** mudo para "clt", **Then** a mudança é
   aceita (nada fica fora de ciclo).
6. **Given** sou "prestador" com um lançamento previsto em "Salário", ou com um salário de data
   futura, **When** tento mudar para "clt", **Then** a mudança é recusada, explicando que o
   salário do CLT é sempre realizado e não pode ter data futura.

---

### Edge Cases

- Virada de ano: o ciclo de dezembro vai de 01/12 a 31/12, o anterior de janeiro é 01/12 do ano
  anterior e o próximo de dezembro é 01/01 do ano seguinte (se não for posterior ao mês atual).
- Lançamento no dia 1 ou no último dia do mês cai naquele mês.
- Consultar um mês futuro para o "prestador" devolve o mês, fechado, sem próximo.
- Lançamento com data futura (ex.: previsto do mês que vem) é aceito para o "prestador" e aparece
  no mês da data.
- Dívidas, depósitos em cartela e importação de extrato não pedem salário ao "prestador".
- Importação: para o "prestador", uma linha confirmada em "Salário" é uma entrada comum e não abre
  ciclo; não existe a recusa "lance o salário antes".
- Trocar entre "clt" e "clt_prestador" não muda nenhum ciclo.
- Ao trocar de "clt" para "prestador", previstos de recorrência já gerados em ciclos de salário
  continuam como estão; o mês atual ganha o previsto só se a recorrência ainda não tiver
  lançamento nele.
- Recorrência em "Salário" continua recusada para todos os tipos (salário não é recorrência).
- Um usuário nunca vê nem muda o tipo de renda de outro; o administrador não vê o tipo de renda.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Todo usuário MUST ter um tipo de renda: "clt", "prestador" ou "clt_prestador".
- **FR-002**: O cadastro MUST aceitar o tipo de renda como opcional; sem ele, o tipo é "clt".
  Contas já existentes MUST passar a ser "clt".
- **FR-003**: O perfil MUST mostrar o tipo de renda e permitir alterá-lo.
- **FR-004**: Para "clt" e "clt_prestador", ciclos, lançamentos, importação, dívidas, cartelas,
  recorrências e limites MUST se comportar exatamente como antes desta feature.
- **FR-005**: Para "prestador", o ciclo de uma data MUST ser o mês do calendário que a contém (do
  dia 1 ao último dia). O ciclo atual MUST ser o mês de hoje, marcado como aberto; os outros meses
  são fechados.
- **FR-006**: Para "prestador", o anterior de um mês MUST ser o dia 1 do mês anterior quando o
  usuário tiver algum lançamento com data anterior ao início do mês; senão, não há anterior. O
  próximo MUST ser o dia 1 do mês seguinte quando o mês seguinte não for posterior ao mês atual;
  senão, não há próximo.
- **FR-007**: Para "prestador", nenhum lançamento (manual, importado, parcela de dívida ou depósito
  em cartela) MUST ser recusado por falta de salário ou por estar antes do primeiro ciclo.
- **FR-008**: Para "prestador", lançamentos em "Salário" MUST ser tratados como entradas comuns:
  podem ser previstos, podem ter data futura e não abrem ciclo.
- **FR-009**: Para "prestador", cada recorrência ativa MUST ter um único previsto por mês, gerado
  no mês atual quando o usuário consulta o ciclo atual ou o resumo, cria um lançamento ou cria uma
  recorrência. A geração MUST ser idempotente.
- **FR-010**: Saldo, gasto por categoria, projeção e limite por categoria MUST usar o ciclo do tipo
  de renda do usuário, com os mesmos filtros de hoje.
- **FR-011**: A troca de "prestador" para "clt" ou "clt_prestador" MUST ser recusada quando: (a)
  existir lançamento que não é salário e o usuário não tiver salário realizado; (b) existir
  lançamento que não é salário com data anterior ao primeiro salário realizado; ou (c) existir
  lançamento em "Salário" previsto ou com data futura. Nos casos (a) e (b), a recusa MUST explicar
  que há lançamentos fora de ciclo; no caso (c), que o salário do CLT é realizado e não futuro.
- **FR-012**: As demais trocas de tipo de renda MUST ser aceitas sem alterar nenhum lançamento.
- **FR-013**: Nenhum ciclo MUST ser guardado: trocar o tipo de renda recalcula os ciclos.
- **FR-014**: O tipo de renda MUST ser visível e alterável só pelo próprio usuário.

### Key Entities

- **Tipo de renda**: atributo do usuário: "clt", "prestador" ou "clt_prestador". Decide a regra do
  ciclo. ("clt_prestador" terá acesso a serviços a receber na feature 013; nesta feature, se
  comporta como "clt".)
- **Ciclo mensal** (derivado, não guardado): mês do calendário, com início, fim, se está aberto e
  os vizinhos anterior e próximo.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Um prestador recém-cadastrado consegue registrar o primeiro gasto em uma única ação,
  sem lançar salário antes.
- **SC-002**: 100% dos testes existentes do fluxo CLT continuam passando sem alteração.
- **SC-003**: Em 100% dos casos de calendário testados (fevereiro de 28 e 29 dias, meses de 30 e 31
  dias, virada de ano, dia 1 e último dia), o ciclo mensal bate com o calendário.
- **SC-004**: Nenhuma troca de tipo de renda deixa um lançamento fora de ciclo.
- **SC-005**: Consultar o ciclo atual várias vezes no mesmo mês nunca duplica um previsto de
  recorrência.

## Assumptions

- Pedido explícito do usuário em 2026-09-30; constituição 4.3.0 (Princípio II).
- Serviços a receber, e a checagem de serviços pendentes ao trocar de "clt_prestador" para "clt",
  ficam para a feature 013.
- O mês é o do fuso `America/Sao_Paulo`, como todas as datas de lançamento.
- A sugestão de valor do salário continua disponível para todos os tipos; é só uma sugestão.
- Escopo: só backend (API). O seletor de tipo de renda e os textos de "mês" no frontend ficam para
  depois.
