<!--
Sync Impact Report
- Version change: 5.0.0 → 5.1.0 (MINOR: lembretes por push no PWA entram no escopo, pedido
  pelo usuário em 2026-10-01)
- Modified principles:
  - V. Contas de Usuário e Isolamento de Dados: lembretes e inscrições de push pertencem ao
    usuário; chaves VAPID entre os segredos
  - VI. Escopo P0 e Simplicidade: regras de lembretes (origens, janela de 3 dias, derivação,
    resumo diário sem valores nem nomes, envio por comando agendado)
- Added sections: nenhuma (Stack ganhou o item "Notificações")
- Removed sections: nenhuma
- Templates: nenhuma alteração
- Follow-up TODOs:
  - CLAUDE.md: glossário (Lembrete, Inscrição de push) e modelo de dados (`lembrete`,
    `inscricao_push`, `envio_lembrete`)
  - Spec 015 (lembretes) via /speckit-specify
- Decisão registrada: o Briefing pede 2 ciclos de uso real antes de qualquer item P1;
  lembretes são P1 e o usuário decidiu seguir mesmo assim.
- Histórico:
  - 4.3.0 → 5.0.0: administrador vê situação das contas, desativa/reativa e vê contagens
    globais de uso (feature 014)
  - 4.2.0 → 4.3.0: tipo de renda e serviços a receber (features 012 e 013)
  - 4.1.0 → 4.2.0: depósito da cartela fora do saldo (`conta_no_saldo = False`)
  - 4.0.1 → 4.1.0: importação de extrato de conta (OFX, CSV ou PDF) com prévia confirmada;
    fatura de cartão nunca importada; salário importado abre ciclo (feature 011)
  - 4.0.0 → 4.0.1: escopo só do backend; API "consumida por clientes HTTP"
  - 3.1.0 → 4.0.0: ciclo aberto pelo salário lançado manualmente (sem dia fixo/dia útil)
  - 3.0.0 → 3.1.0: papel de administrador restrito a reset de senha
  - 2.0.0 → 3.0.0: multiusuário na web (cadastro aberto, login com e-mail e senha,
    isolamento por usuário)
-->

# Gerencia Constitution

## Core Principles

### I. Integridade Financeira (INEGOCIÁVEL)

O sistema responde quanto entrou, para onde foi e quanto sobrou. Um centavo errado é um
defeito crítico.

- Todo valor monetário MUST ser `int` em centavos, em todas as camadas: modelos, colunas
  (`INTEGER`/`BIGINT`), schemas, JSON, testes e clientes. `float` e `Decimal` são proibidos
  para dinheiro.
- Nada MUST contar duas vezes no saldo. Cartão de crédito entra no saldo só como a fatura
  total (saída na categoria "Cartão de crédito"); lançamentos pagos no cartão, inclusive
  parcelas, MUST ter `conta_no_saldo = False`. Extrato de fatura de cartão MUST NOT ser
  importado (cada compra já está na fatura); só extrato de conta é aceito.
- Saldo do ciclo (sempre de um único usuário) = entradas − saídas, considerando só
  `status = realizado` e `conta_no_saldo = True`. Gasto por categoria usa o mesmo filtro. Saldos MUST ser
  derivados dos lançamentos, nunca armazenados.
- Parcelas: cada uma recebe `valor_total // parcelas`; o resto de centavos vai para a
  última. A soma das parcelas MUST ser igual a `valor_total`.
- Cartela: N é o maior inteiro com `base × N(N+1)/2 ≤ meta`; o resto vira uma casa com
  `is_ajuste = True`. A soma das casas MUST ser igual à meta. Depósito numa casa MUST
  gerar um lançamento `saida` na categoria "Poupança" com `conta_no_saldo = False`: o
  dinheiro guardado continua do usuário, então não sai do saldo nem conta como gasto.
- Operações que gravam mais de um registro financeiro (ex.: gerar parcelas, depositar em
  casa) MUST ocorrer numa única transação.

**Rationale**: centavos inteiros eliminam erro de arredondamento; contagem dupla e somas
que não fecham tornam o saldo inútil para decidir.

### II. Ciclo Derivado do Tipo de Renda

Todo usuário tem um tipo de renda (`tipo_renda`), escolhido no cadastro e editável no
perfil: `clt` (só salário), `prestador` (só presta serviço) ou `clt_prestador` (os dois).
O tipo de renda define como o ciclo é derivado.

- **`clt` e `clt_prestador` — ciclo aberto pelo salário lançado:**
  - O ciclo começa quando o usuário lança o salário, à mão ou numa linha de extrato que ele
    confirma na categoria "Salário". Cada lançamento de salário que abre ciclo inicia um
    ciclo, que vai da data desse lançamento até a véspera do próximo lançamento que abre
    ciclo. O ciclo mais recente fica aberto, sem data de fim. Salário importado segue as
    mesmas regras do lançado à mão (data não futura, nenhum lançamento fora de ciclo).
  - Enquanto o usuário não tiver lançado o primeiro salário, o sistema MUST recusar outros
    lançamentos e orientar a lançar o salário para abrir o primeiro ciclo.
- **`prestador` — ciclo pelo mês do calendário:**
  - Cada ciclo vai do dia 1 ao último dia de um mês, derivado da data de referência. O
    ciclo atual é o mês que contém a data de hoje.
  - Nenhum salário é exigido para lançar. "Salário" é uma entrada comum e MUST NOT abrir
    ciclo.
  - Recorrências geram o previsto do mês de forma idempotente, sem depender de um
    lançamento que abra o ciclo.
- A troca de `prestador` para `clt` ou `clt_prestador` MUST ser recusada se deixar algum
  lançamento fora de um ciclo de salário. As demais trocas de tipo recalculam os ciclos
  sem migrar dados.
- O sistema MUST NOT prever nem calcular o dia do pagamento (sem dia fixo, dia útil ou
  feriados).
- O ciclo MUST ser derivado (das datas dos lançamentos que abrem ciclo ou do mês do
  calendário), de cada usuário. MUST NOT existir tabela, coluna ou cache persistido de
  ciclo; corrigir a data ou excluir um lançamento que abre ciclo, ou trocar o tipo de
  renda, recalcula os ciclos.
- Datas de lançamento MUST ser `date`, sem hora, no fuso `America/Sao_Paulo`.
- Recorrências geram lançamentos previstos por ciclo; a regra de geração e a regra de
  ciclo de cada tipo de renda vivem no domínio.

**Rationale**: para quem tem salário, o dinheiro só está disponível quando entra de fato,
e abrir o ciclo pelo lançamento real evita erro de configuração de data. Quem presta
serviço recebe vários pagamentos soltos; o mês do calendário dá um período estável sem
depender de um pagamento específico. Derivar o ciclo mantém uma única fonte da verdade.

### III. Domínio Puro e Teste Primeiro

- Regras de negócio (ciclo, saldo, parcelas, cartela, recorrências) MUST viver em
  `app/domain/` como funções puras, sem acesso a banco, rede ou relógio implícito (a data
  de referência é parâmetro).
- Toda regra de domínio MUST nascer com teste escrito antes da implementação
  (vermelho → verde → refatorar), em `tests/domain/`.
- Testes de domínio MUST cobrir casos-limite: zero, resto de centavos, 1 parcela, meta
  menor que a base, virada de mês e de ano, lançamento no mesmo dia de um salário, ciclo
  aberto sem fim, primeiro ciclo e exclusão ou mudança de data de um salário.
- Endpoints MUST ter testes de API (`tests/api/`). Testes de integração MUST rodar contra
  PostgreSQL real (ex.: container), não SQLite.
- Mudança com teste falhando MUST NOT ser mesclada.

**Rationale**: regra pura é barata de testar exaustivamente; o teste primeiro prova que a
regra foi entendida antes de ser codificada.

### IV. API com Contratos Tipados

O projeto é uma API HTTP (FastAPI) consumida por clientes HTTP; não renderiza HTML. O frontend
é um cliente separado dessa API.

- Todo endpoint MUST declarar schemas Pydantic de entrada e saída; `dict` cru e `Any` são
  proibidos nas respostas.
- Valores monetários trafegam como inteiros em centavos; formatação em reais é
  responsabilidade do cliente.
- O OpenAPI gerado é o contrato da API; mudanças incompatíveis MUST ser registradas no plano
  da feature que as introduz.
- Erros MUST seguir um formato único, com status HTTP coerente (ex.: 400, 401, 403, 404,
  409, 415, 422, 429, 500).

**Rationale**: contrato explícito evita divergência entre a API e quem a consome e permite
gerar tipos no cliente.

### V. Contas de Usuário e Isolamento de Dados

O sistema roda na web e é multiusuário: qualquer pessoa pode se cadastrar.

- Login MUST ser feito com e-mail e senha. O e-mail MUST ser único entre os usuários.
- Senhas MUST ser armazenadas com hash forte (argon2 ou bcrypt); nunca em texto claro nem
  devolvidas pela API.
- Todo endpoint, exceto saúde (health), cadastro e login, MUST exigir usuário autenticado.
- Todo dado financeiro (configuração, categorias, lançamentos, recorrências, dívidas,
  cartelas, casas, serviços a receber), assim como lembretes e inscrições de push, MUST
  pertencer a um usuário, e toda consulta MUST ser filtrada pelo usuário autenticado. Acessar dado de outro usuário MUST retornar 404, e isso MUST ter
  teste.
- Dados pessoais do cadastro (nome, e-mail, telefone, etc.) MUST ser visíveis só ao próprio
  usuário, com a única exceção do papel de administrador descrita abaixo.
- Segredos (credenciais de banco, chaves de token, chaves VAPID de push) MUST vir de variáveis de ambiente e
  MUST NOT ser versionados.
- Logs MUST NOT conter senhas, tokens, dados pessoais ou valores e descrições de
  lançamentos.
- Existem só dois papéis: usuário e administrador. Novos papéis ou permissões MUST NOT ser
  criados sem pedido explícito.
- Administrador:
  - MUST NOT ser criado pelo cadastro público; só por comando no servidor ou configuração
    de deploy.
  - Pode ver apenas nome, e-mail, data de criação e situação (ativa ou desativada) das
    contas, e MUST NOT ter acesso a dados financeiros de um usuário nem aos demais dados
    pessoais (telefone, cargo, data de nascimento).
  - Pode ver contagens globais de uso, somadas entre todos os usuários: contas, lançamentos,
    entradas e saídas por mês e dívidas por forma de pagamento. Essas contagens MUST NOT
    trazer valores em reais nem ser quebradas por usuário.
  - As ações administrativas permitidas são:
    - resetar senha: o sistema gera uma senha temporária aleatória, exibida uma única vez ao
      administrador, encerra as sessões do usuário e obriga a troca de senha no próximo
      login. O administrador MUST NOT escolher a senha de outro usuário;
    - desativar conta: encerra as sessões e recusa o login, sem apagar dados; e reativar.
  - Toda ação administrativa MUST ser registrada (quem, o quê, em quem, quando).

**Rationale**: dados financeiros e pessoais de várias pessoas no mesmo banco tornam o
vazamento entre usuários o pior modo de falha possível do sistema.

### VI. Escopo P0 e Simplicidade

- Só funcionalidades P0 MUST ser implementadas. P1/P2 e "preparar para o futuro" exigem
  pedido explícito.
- Sem IA no MVP. Todo lançamento é manual ou importado de extrato de conta (OFX, CSV ou PDF).
  Importação MUST passar por uma prévia em que o usuário revisa e confirma cada linha antes
  de gravar; nada é gravado sem essa confirmação. A sugestão de categoria na prévia MUST
  ser uma regra determinística (ex.: última categoria usada com a mesma descrição), nunca
  IA. Linhas importadas seguem as mesmas regras de um lançamento manual.
- Lançamento tem só valor, categoria e data como campos obrigatórios; novos campos
  obrigatórios MUST NOT ser adicionados.
- Serviço a receber (cliente, valor, data prevista, categoria de entrada que não seja
  "Salário") existe só para `prestador` e `clt_prestador`. Ele gera uma entrada prevista
  que vira realizada quando o usuário marca o recebimento. Sua situação (a receber,
  atrasado, recebido) MUST ser derivada do lançamento e da data, nunca armazenada.
- Lembretes têm três origens:
  - contas a pagar: saídas previstas com `conta_no_saldo = True` e data até hoje + 3 dias,
    incluindo as atrasadas;
  - valores a receber: entradas previstas na mesma janela;
  - lembretes livres: texto e data criados pelo usuário.
  Contas a pagar e valores a receber MUST ser derivados dos lançamentos previstos, nunca
  armazenados; só o lembrete livre tem tabela própria.
- O envio é um resumo diário por usuário, por Web Push (VAPID), para os aparelhos que ele
  inscreveu, por volta das 8h em `America/Sao_Paulo` e no máximo uma vez por dia. O envio
  MUST ser disparado por um comando agendado (cron) do próprio código, nunca dentro de uma
  requisição da API.
- A notificação MUST NOT conter valores em reais, descrições de lançamentos nem nomes de
  pessoas ou clientes: só contagens e texto genérico. Os detalhes ficam na página de
  lembretes, atrás do login.
- Camadas: `api/routes/` só valida e chama `services/`; `services/` lê e grava no banco e
  chama `domain/`; regra de negócio MUST NOT ficar em rotas nem em services.
- Um único serviço (monólito). Filas, caches ou serviços extras MUST ser justificados no
  plano da feature. YAGNI.

**Rationale**: o problema central é saber para onde o dinheiro vai; tudo que não serve a
isso atrasa o MVP.

## Stack e Restrições Técnicas

- **Linguagem**: Python 3.12+ (ambiente atual 3.14), tipagem em todo código, gerenciado
  com `uv`.
- **Framework**: FastAPI + Pydantic v2; settings com pydantic-settings.
- **Banco de dados**: PostgreSQL, SQLAlchemy 2.x e Alembic. Trocar essas escolhas exige
  emenda desta seção.
- **Migrações**: toda mudança de schema MUST ser feita por migração Alembic versionada e
  reversível (com `downgrade`).
- **Testes**: pytest (httpx/TestClient para a API).
- **Qualidade**: ruff para lint e formatação.
- **Nomes**: domínio em português (`lancamento`, `cartela`, `casa`); infraestrutura pode
  ser em inglês.
- **Frontend**: Next.js + shadcn/ui, em escopo desde 2026-09-28; consome só a API e segue
  o Princípio I (dinheiro em centavos `int`, formatado em reais só na exibição).
- **Notificações**: Web Push com VAPID, enviado pelo backend com `pywebpush`; o frontend
  registra um service worker para receber e abrir as notificações.

## Fluxo de Desenvolvimento

- Features seguem o fluxo Spec Kit: `/speckit-specify` → `/speckit-plan` →
  `/speckit-tasks` → `/speckit-implement`. O plano MUST passar pelo "Constitution Check"
  antes da implementação.
- Trabalho grande MUST ter plano curto aprovado antes de implementar; pedido ambíguo ou
  contrário a esta constituição MUST ser questionado, não suposto.
- Critérios para merge:
  1. `uv run pytest` passando (Princípio III).
  2. `uv run ruff check .` sem erros e código formatado.
  3. Migração incluída e testada quando houver mudança de schema.
  4. Contrato OpenAPI revisado quando houver mudança de endpoint (Princípio IV).
- Commits pequenos, em Conventional Commits (`feat:`, `fix:`, `test:`, `refactor:`,
  `docs:`).
- Arquivos de documentação extras MUST NOT ser criados sem pedido.

## Governance

- Esta constituição prevalece sobre outras práticas do projeto, inclusive o `CLAUDE.md`.
  Em conflito, ela vence ou deve ser emendada; o `CLAUDE.md` MUST ser mantido coerente.
- Emendas MUST ser feitas via `/speckit-constitution`, registrando no Sync Impact Report o
  que mudou e o impacto nos templates.
- Versionamento semântico:
  - MAJOR: remoção ou redefinição incompatível de princípio.
  - MINOR: novo princípio ou seção, ou expansão material.
  - PATCH: esclarecimentos e ajustes de redação.
- Toda revisão MUST verificar conformidade com os princípios. Violações só são aceitas com
  justificativa registrada na seção "Complexity Tracking" do plano da feature.

**Version**: 5.1.0 | **Ratified**: 2026-09-28 | **Last Amended**: 2026-10-01
