# Feature Specification: Importação de Extrato

**Feature Branch**: `011-importacao-extrato`

**Created**: 2026-09-29

**Status**: Draft

**Input**: Pedido explícito do usuário (item P2 do Briefing, "Importação de extrato (OFX/CSV)"):
"O cliente deve escolher o seu banco; o importante é sempre poder trazer o histórico do banco do
usuário através dos extratos." Fluxo decidido em 2026-09-29: prévia + confirmação, com categoria
sugerida pelo histórico, sem IA. Formatos: "precisamos aceitar os 3 formatos mais usados para se
adequar ao padrão das empresas" (OFX, CSV e PDF). Bancos com exemplo fornecido: Itaú, Nubank,
Inter, Mercado Pago e Neon. Constituição emendada para 4.1.0 para permitir a importação.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Importar um extrato e revisar antes de gravar (Priority: P1)

Escolho meu banco, envio o extrato da conta e vejo uma prévia com todas as movimentações: data,
valor, descrição, se é entrada ou saída e uma categoria sugerida. Ajusto as categorias, desmarco o
que não quero e confirmo. Só o que confirmei vira lançamento.

**Why this priority**: é a feature: trazer o histórico do banco sem digitar linha por linha, sem
perder o controle do que entra no sistema.

**Independent Test**: com um salário já lançado, enviar um extrato OFX com 5 movimentações
posteriores ao salário, conferir a prévia, trocar uma categoria, desmarcar uma linha, confirmar e
ver 4 lançamentos novos no ciclo.

**Acceptance Scenarios**:

1. **Given** um extrato válido, **When** envio o arquivo escolhendo o banco, **Then** vejo a
   prévia com uma linha por movimentação, com data, valor em centavos, descrição e tipo
   (crédito = entrada, débito = saída), e nada é gravado ainda.
2. **Given** a prévia, **When** confirmo as linhas escolhidas com suas categorias, **Then** cada
   linha vira um lançamento realizado com o valor, a data, a descrição e a categoria escolhida.
3. **Given** a prévia, **When** desmarco linhas, **Then** elas não viram lançamento.
4. **Given** uma linha de débito, **When** escolho uma categoria de entrada para ela (ou o
   contrário), **Then** a confirmação recusa essa linha e explica o motivo; nada do lote é gravado.
5. **Given** um arquivo que não é um extrato válido do formato escolhido, **When** o envio,
   **Then** o sistema recusa e explica o problema, sem gravar nada.
6. **Given** um valor com separador de milhar e decimal (ex.: "-1.234,56"), **When** vejo a
   prévia, **Then** o valor aparece exato em centavos (123456, saída).

---

### User Story 2 - Trazer o histórico, inclusive os salários (Priority: P1)

Envio extratos de meses anteriores. Nas linhas de salário escolho a categoria "Salário", e ao
confirmar os ciclos do passado passam a existir, com os gastos de cada período dentro deles.

**Why this priority**: o usuário pediu explicitamente para trazer o histórico; sem salários
importados, nenhuma linha anterior ao primeiro salário lançado à mão seria aceita.

**Independent Test**: usuário novo, sem salário; importar um extrato de 3 meses com 3 salários e
gastos; confirmar e ver 3 ciclos com os gastos em cada um.

**Acceptance Scenarios**:

1. **Given** um usuário sem nenhum salário, **When** importo um extrato em que marco as linhas de
   salário como "Salário", **Then** a confirmação aceita o lote e os ciclos passam a começar nas
   datas desses salários.
2. **Given** um extrato em que há gastos antes do primeiro salário (no sistema ou no próprio
   lote), **When** vejo a prévia, **Then** essas linhas aparecem marcadas como "antes do primeiro
   ciclo" e desmarcadas; se eu as confirmar mesmo assim, a confirmação recusa o lote.
3. **Given** salários importados de meses passados, **When** confirmo, **Then** não são gerados
   gastos fixos previstos para esses ciclos fechados.
4. **Given** um salário importado mais recente que todos os salários do sistema, **When** confirmo,
   **Then** ele abre o novo ciclo aberto e os gastos fixos previstos desse ciclo são gerados, como
   num lançamento manual.
5. **Given** uma linha marcada como "Salário" com data futura, **When** confirmo, **Then** o lote é
   recusado.

---

### User Story 3 - Importar de novo sem duplicar (Priority: P1)

Posso enviar extratos que se sobrepõem (ex.: o mês inteiro e depois de novo o mesmo mês) sem
criar lançamentos repetidos. Gastos que já lancei à mão aparecem sinalizados.

**Why this priority**: o usuário vai reimportar; duplicar lançamentos quebra o saldo (Princípio I).

**Independent Test**: importar o mesmo arquivo duas vezes; na segunda prévia todas as linhas vêm
como "já importadas" e desmarcadas.

**Acceptance Scenarios**:

1. **Given** um extrato já importado, **When** envio o mesmo arquivo de novo, **Then** todas as
   linhas aparecem como "já importada", desmarcadas, e confirmá-las não cria nada.
2. **Given** um extrato que cobre um período parcialmente importado, **When** vejo a prévia,
   **Then** só as linhas novas vêm marcadas.
3. **Given** um gasto lançado à mão com a mesma data, tipo e valor de uma linha do extrato,
   **When** vejo a prévia, **Then** a linha aparece como "possível duplicada", desmarcada, e posso
   marcá-la se for de fato outro gasto.
4. **Given** duas movimentações idênticas no mesmo dia no extrato (ex.: dois cafés de R$ 8,00),
   **When** importo, **Then** as duas viram lançamentos, e reimportar não cria uma terceira.

---

### User Story 4 - Escolher o banco e o formato (Priority: P1)

Escolho meu banco numa lista e o formato do arquivo que baixei: OFX, CSV ou PDF. Para os bancos
suportados o sistema já sabe ler os três formatos que o banco oferece; para qualquer outro banco,
envio o OFX ou um CSV informando quais colunas são data, valor e descrição.

**Why this priority**: o usuário pediu os três formatos mais usados, e três dos cinco bancos dele
só entregaram PDF.

**Independent Test**: listar os bancos; importar o PDF de cada banco suportado e ver a prévia com
as mesmas movimentações do extrato; importar um CSV genérico informando as colunas.

**Acceptance Scenarios**:

1. **Given** qualquer usuário, **When** peço a lista de bancos, **Then** vejo Itaú, Nubank, Inter,
   Mercado Pago e Neon, cada um com os formatos aceitos, e a opção "Outro banco" (OFX ou CSV
   genérico).
2. **Given** o extrato em PDF de um banco suportado, **When** o envio, **Then** a prévia traz
   todas as movimentações do período, sem as linhas de saldo, totais do dia, cabeçalhos e rodapés,
   com descrições que ocupam várias linhas juntadas numa só.
3. **Given** um PDF de outro banco ou de layout diferente do esperado, **When** o envio escolhendo
   um banco, **Then** o sistema recusa e sugere enviar em OFX ou CSV.
4. **Given** um PDF que é imagem escaneada, sem texto, **When** o envio, **Then** o sistema recusa
   e explica que só lê PDF gerado pelo banco.
5. **Given** um CSV genérico, **When** informo as colunas de data, valor e descrição, o formato da
   data e o separador decimal, **Then** a prévia lê as linhas corretamente.
6. **Given** um CSV com valores de entrada e saída em colunas separadas (crédito e débito),
   **When** informo as duas colunas, **Then** o tipo de cada linha vem da coluna preenchida.

---

### User Story 5 - Categoria sugerida pelo meu histórico (Priority: P2)

Na prévia, cada linha já vem com a categoria que usei da última vez para uma descrição igual, para
eu só conferir.

**Why this priority**: reduz o trabalho a cada importação; sem ela a feature funciona, só com mais
cliques.

**Independent Test**: importar um extrato, categorizar "UBER TRIP" como Transporte; importar outro
extrato com "UBER TRIP" e ver Transporte sugerido.

**Acceptance Scenarios**:

1. **Given** lançamentos anteriores com a descrição "UBER TRIP" em Transporte, **When** uma linha
   do extrato tem "Uber Trip" (diferença só de maiúsculas, acentos ou espaços), **Then** a sugestão
   é Transporte.
2. **Given** a mesma descrição usada em duas categorias, **When** vejo a prévia, **Then** a sugestão
   é a do lançamento mais recente.
3. **Given** uma descrição nunca vista, **When** vejo a prévia, **Then** não há sugestão e a linha
   precisa de categoria antes de ser confirmada.
4. **Given** uma sugestão de categoria desativada, **When** vejo a prévia, **Then** não há sugestão.

---

### Edge Cases

- Extrato de fatura de cartão de crédito: proibido pela constituição; a lista de bancos só oferece
  extratos de conta, e o sistema avisa que a fatura entra como um gasto único em "Cartão de
  crédito".
- Linha de pagamento da fatura no extrato da conta: importada como qualquer saída; o usuário
  escolhe "Cartão de crédito" (se tiver criado a categoria).
- Linha com valor zero: aparece como inválida e não pode ser confirmada.
- Movimentações de saldo, aplicação/resgate automático ou transferência entre contas próprias:
  aparecem como linhas comuns; o usuário desmarca as que não quer.
- Arquivo em codificação antiga (latin-1) com acentos: descrições aparecem corretas.
- Mesmo mês importado primeiro em PDF e depois em OFX: as linhas do OFX aparecem como possíveis
  duplicadas, desmarcadas.
- Extrato com hora na movimentação (ex.: Neon): só a data é usada.
- Linhas de rendimento automático, juros ou tarifa da conta: aparecem como movimentações comuns.
- O banco muda o layout do PDF: o arquivo é recusado com orientação para usar OFX ou CSV, em vez de
  gerar linhas erradas.
- Arquivo muito grande (mais de 2 MB) ou com mais de 5.000 linhas: recusado com orientação para
  dividir o período.
- Depósito em cartela não é criado por importação: uma linha em "Poupança" vira saída comum.
- Um usuário nunca vê a prévia, as sugestões nem os lançamentos importados de outro; a detecção de
  "já importada" só compara com os lançamentos do próprio usuário.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST aceitar extratos de conta em OFX, CSV e PDF.
- **FR-002**: O sistema MUST listar os bancos disponíveis, cada um com os formatos que aceita, e a
  opção "Outro banco" com OFX e CSV genérico. Bancos suportados: Itaú (PDF, OFX), Nubank (OFX, CSV,
  PDF), Inter (OFX, CSV, PDF), Mercado Pago (PDF) e Neon (PDF); os demais formatos de cada banco
  entram quando houver arquivo de exemplo.
- **FR-002a**: A leitura de PDF MUST ser específica por banco, MUST descartar linhas que não são
  movimentação (saldo do dia, totais, cabeçalho, rodapé) e MUST juntar descrições quebradas em
  várias linhas. PDF sem texto ou de layout não reconhecido MUST ser recusado com orientação para
  usar OFX ou CSV.
- **FR-003**: No CSV genérico, o usuário MUST informar as colunas de data, descrição e valor (ou
  crédito e débito separados), o formato da data e o separador decimal.
- **FR-004**: Enviar um extrato MUST produzir uma prévia sem gravar nada.
- **FR-005**: Cada linha da prévia MUST trazer data, valor em centavos inteiros, tipo (entrada ou
  saída), descrição, categoria sugerida (ou nenhuma) e situação: nova, já importada, possível
  duplicada, antes do primeiro ciclo ou inválida.
- **FR-006**: Valores MUST ser convertidos do texto do extrato para centavos exatos, sem
  arredondamento.
- **FR-007**: Só as linhas que o usuário confirma, com a categoria escolhida por ele, MUST virar
  lançamentos realizados.
- **FR-008**: A confirmação MUST gravar todas as linhas ou nenhuma: qualquer linha recusada recusa
  o lote e informa quais linhas e por quê.
- **FR-009**: Linhas confirmadas MUST seguir as regras do lançamento manual: categoria ativa do
  usuário, tipo da categoria igual ao tipo da linha, salário com data não futura e nenhum
  lançamento fora de ciclo, considerando o lote inteiro.
- **FR-010**: Salários confirmados MUST abrir ciclos; previstos de recorrência MUST ser gerados só
  se o lote abrir um novo ciclo aberto, como no lançamento manual.
- **FR-011**: Cada lançamento importado MUST guardar uma identificação da movimentação de origem
  (o identificador do banco quando o arquivo traz um; senão, uma combinação de banco, data, valor,
  descrição e ordem da linha no dia), e uma mesma movimentação MUST NOT ser importada duas vezes
  pelo mesmo usuário a partir do mesmo formato. Entre formatos diferentes do mesmo banco, a
  proteção é a sinalização de possível duplicada (FR-012).
- **FR-012**: A prévia MUST sinalizar como possível duplicada a linha que não foi importada antes,
  mas tem a mesma data, tipo e valor de um lançamento do usuário (lançado à mão ou importado de
  outro formato).
- **FR-013**: A categoria sugerida MUST ser a do lançamento mais recente do usuário com a mesma
  descrição normalizada (sem diferença de maiúsculas, acentos e espaços), se a categoria estiver
  ativa e for do mesmo tipo; nunca por IA.
- **FR-014**: O sistema MUST recusar arquivos acima de 2 MB ou 5.000 linhas, e arquivos que não
  possam ser lidos no formato escolhido.
- **FR-015**: Extrato de fatura de cartão MUST NOT ser oferecido nem aceito.
- **FR-016**: Lançamentos importados MUST ser editáveis e excluíveis como qualquer lançamento.
- **FR-017**: Prévia, sugestões e confirmação MUST usar só dados do usuário autenticado.

### Key Entities

- **Extrato**: arquivo enviado pelo usuário (OFX ou CSV) com as movimentações de uma conta num
  período; não é guardado.
- **Linha da prévia** (não guardada): movimentação lida do extrato, com situação e categoria
  sugerida.
- **Banco**: nome e formatos aceitos (OFX, CSV com layout próprio, PDF com layout próprio ou CSV
  genérico).
- **Lançamento importado**: lançamento comum com a identificação da movimentação de origem.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Importar um extrato de um mês (até 200 movimentações) leva menos de 2 minutos do
  envio à confirmação, com a prévia em menos de 3 segundos.
- **SC-002**: Reimportar o mesmo extrato cria zero lançamentos novos em 100% dos casos.
- **SC-003**: Em 100% das linhas, o valor em centavos bate com o do extrato.
- **SC-004**: Depois de importar um período completo, o saldo do ciclo bate com a variação do saldo
  da conta no banco no mesmo período, descontadas as linhas que o usuário desmarcou.
- **SC-005**: A partir da segunda importação, a maioria das linhas recorrentes (mesma descrição)
  já vem com a categoria certa sugerida.

## Assumptions

- Pedido explícito do usuário em 2026-09-29, item P2 do Briefing; constituição 4.1.0 permite a
  importação com prévia confirmada.
- Depende das features 001 (lançamentos e ciclo), 005 (categorias), 006 (recorrências) e 009
  (limites: lançamentos importados contam no limite como qualquer outro; o aviso de limite não é
  mostrado na importação).
- Os leitores por banco foram modelados a partir dos extratos reais do usuário (pasta `extratos/`,
  fora do versionamento); os testes usam cópias sintéticas com o mesmo layout e sem dados reais.
- PDF é o formato mais frágil: um leitor por banco, que pode quebrar se o banco mudar o layout.
  OFX, quando o banco oferece, é o mais confiável.
- Uma importação é de uma única conta; várias contas são importadas em envios separados.
- Não há integração direta com o banco (Open Finance): o usuário baixa o extrato e envia o arquivo.
- A prévia não é guardada; se o usuário sair antes de confirmar, envia o arquivo de novo.
- O frontend ganha uma tela de importação: escolha do banco, envio do arquivo, tabela de prévia com
  categoria editável e confirmação.
