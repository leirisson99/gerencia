# CLAUDE.md

Guia para o Claude trabalhar neste repositório. Leia inteiro antes de qualquer tarefa.

## O projeto

Sistema web de controle financeiro pessoal organizado em torno do **ciclo**: aberto pelo salário para quem é CLT, ou o mês do calendário para quem presta serviço. Ele responde a três perguntas: quanto entrou, para onde foi (por categoria) e quanto sobrou. O que sobra alimenta **cartelas de poupança** por meta, sem prazo.

- **Escopo:** backend (API FastAPI) e frontend (Next.js + shadcn/ui, em `../frontend`, desde 2026-09-28). Regras e critérios precisam ser verificáveis pela API.
- Multiusuário na web: qualquer pessoa pode se cadastrar; cada usuário só vê os próprios dados.
- Login com e-mail e senha. Um único administrador, que só pode resetar senhas.
- Problema central: não saber para onde o dinheiro vai.
- Tudo é lançado manualmente no MVP, inclusive o salário, que abre o ciclo de quem é CLT.
- Três tipos de renda: `clt`, `prestador` e `clt_prestador` (escolhido no cadastro, editável no perfil).

**Fonte da verdade:** `.specify/memory/constitution.md`. Se uma instrução aqui ou num pedido contrariar a constituição, pare e aponte o conflito antes de implementar.

## Regras que você nunca quebra

1. **Dinheiro em centavos, como `int`.** Nunca `float`, nem em testes, schemas ou JSON da API.
2. **O ciclo é derivado, não armazenado.** Ele começa na data de cada salário lançado. Não crie tabela nem coluna de ciclo.
3. **Nada conta duas vezes no saldo.** Cartão entra só como fatura total. Parcela paga no cartão usa `conta_no_saldo = False`.
4. **Regra de domínio nasce com teste.** Escreva o teste antes (ciclo, cartela, parcelas, recorrências, saldo).
5. **Todo dado financeiro pertence a um usuário.** Toda consulta filtra pelo usuário autenticado; dado de outro usuário retorna 404, com teste.
6. **Só P0.** Não implemente P1/P2 nem "prepare para o futuro" sem pedido explícito.
7. **Lançamento tem só valor, categoria e data como obrigatórios.** Não adicione campos obrigatórios.
8. **Sem IA no MVP.** Lançamentos são manuais ou importados de extrato de conta (OFX, CSV ou PDF), sempre com prévia confirmada pelo usuário. Sugestão de categoria só por regra fixa. Extrato de fatura de cartão nunca é importado.

## Glossário do domínio

| Termo | Significado |
| --- | --- |
| Tipo de renda | `clt` (só salário), `prestador` (só presta serviço) ou `clt_prestador` (os dois). Define a regra do ciclo e o acesso a Serviços |
| Ciclo | `clt` e `clt_prestador`: da data de um salário lançado até a véspera do próximo; o mais recente fica aberto, sem fim. `prestador`: mês do calendário (dia 1 ao último dia) |
| Salário | Lançamento de entrada na categoria de sistema "Salário". É o único que abre ciclo, e só para `clt` e `clt_prestador`. Para `prestador`, é uma entrada comum |
| Lançamento | Movimento de dinheiro: `entrada` ou `saida`, `previsto` ou `realizado` |
| Recorrência | Gasto ou renda fixa que gera um previsto por ciclo (aluguel, internet). O salário não é recorrência |
| Serviço | Serviço a receber de um cliente (só `prestador` e `clt_prestador`). Gera uma entrada prevista na data prevista; vira realizada ao marcar o recebimento. Situação derivada: a receber, atrasado, recebido |
| Entrada inesperada | Lançamento manual de entrada (freela, 13º, reembolso, venda, presente) em categoria que não abre ciclo |
| Dívida | `devo` ou `me_devem`, com N parcelas geradas como lançamentos previstos |
| Fatura | Pagamento total do cartão, lançado como uma saída na categoria "Cartão de crédito" |
| Cartela | Meta de poupança dividida em casas sequenciais (base × 1…N) + casa de ajuste |
| Casa | Um depósito da cartela. Livre ou depositada |
| Importação | Extrato de conta (OFX, CSV ou PDF) lido numa prévia; só as linhas que o usuário confirma viram lançamentos, com as mesmas regras do lançamento manual |
| Administrador | Papel criado só no servidor; vê nome, e-mail e data de criação das contas e só reseta senha |

## Modelo de dados

| Tabela | Campos principais |
| --- | --- |
| `usuario` | nome, email (único), senha_hash, telefone, cargo, data_nascimento (opcional), papel (`usuario` / `admin`), tipo_renda (`clt` / `prestador` / `clt_prestador`), troca_senha_obrigatoria, criado_em |
| `categoria` | usuario_id, nome (único por usuário, sem diferenciar maiúsculas), tipo (`entrada` / `saida`), ativa, sistema. "Salário" e "Poupança" são de sistema e protegidas |
| `recorrencia` | usuario_id, categoria_id, descricao, valor, tipo, dia, ativa |
| `divida` | usuario_id, categoria_id, descricao, pessoa, direcao, valor_total, parcelas, forma_pagamento, dia_vencimento, data_inicio |
| `lancamento` | usuario_id, data, valor, tipo, categoria_id, descricao, status, conta_no_saldo, recorrencia_id, divida_id, parcela_num |
| `cartela` | usuario_id, nome, meta, valor_base, criada_em |
| `casa` | cartela_id, valor, ordem, is_ajuste, depositado_em, lancamento_id |
| `servico` | usuario_id, categoria_id, cliente, descricao, valor, data_prevista, lancamento_id, criado_em |
| `sessao`, `tentativa_login`, `acao_admin` | sessão em cookie, bloqueio de login e auditoria do administrador |

Todos os campos de valor são `int` em centavos. Não existe tabela de configuração de pagamento. A `forma_pagamento` fica na dívida, não no lançamento. Specs de cada feature em `specs/`.

## Regras de cálculo

- **Ciclo (`clt`, `clt_prestador`):** começa em cada data distinta de salário e termina na véspera da próxima. Antes do primeiro salário, nenhum outro lançamento é aceito.
- **Ciclo (`prestador`):** mês do calendário que contém a data; não exige salário. Trocar de `prestador` para outro tipo só é aceito se todos os lançamentos ficarem dentro de um ciclo de salário.
- **Saldo do ciclo** = soma das entradas − soma das saídas, considerando só `status = realizado` e `conta_no_saldo = True`.
- **Gasto por categoria** usa o mesmo filtro, agrupado por `categoria_id`.
- **Recorrências:** um previsto por recorrência em cada ciclo, na próxima ocorrência do dia a partir do início do ciclo, gerado quando o ciclo abre (no `prestador`, de forma idempotente ao usar o mês).
- **Serviço:** a situação é derivada: `recebido` se o lançamento estiver realizado; senão `atrasado` se `data_prevista < hoje`, ou `a_receber`.
- **Cartela:** N = maior inteiro com `base × N(N+1)/2 ≤ meta`. O resto vira uma casa com `is_ajuste = True`. A soma das casas é sempre igual à meta.
- **Parcelas:** `valor_total // parcelas` em cada uma. O resto de centavos vai para a última.
- **Depósito na cartela** gera um lançamento `saida` na categoria "Poupança" com `conta_no_saldo = False`: não sai do saldo nem conta como gasto.

## Estrutura

```text
backend/
  .specify/
    memory/constitution.md
  app/
    main.py            # FastAPI app
    config.py          # settings (pydantic-settings)
    db.py              # engine e sessão
    models/            # SQLAlchemy
    schemas/           # Pydantic (entrada/saída da API)
    domain/            # regras puras, sem banco: ciclo.py, cartela.py, parcelas.py, saldo.py
    services/          # orquestra domain + banco
    api/routes/        # endpoints finos, sem regra de negócio
  alembic/
  tests/
    domain/            # testes das regras puras (a maioria dos testes vive aqui)
    api/
  specs/               # specs das features (Spec Kit)
frontend/              # Next.js + shadcn/ui (repositório irmão ../frontend)
```

**Onde colocar código:** regra de negócio vai em `domain/` (funções puras). `services/` busca e grava dados e chama `domain/`. Rotas só validam entrada e chamam `services/`.

## Comandos

```bash
# rodar dentro de backend/, com Docker Desktop aberto
cp .env.example .env
docker compose up -d db          # PostgreSQL 17 com os bancos gerencia e gerencia_test
uv sync
uv run uvicorn app.main:app --reload
uv run pytest
uv run ruff check . && uv run ruff format .
uv run alembic revision --autogenerate -m "mensagem"
uv run alembic upgrade head
uv run python -m app.cli criar-admin --nome ... --email ... --telefone ... --cargo ...   # único admin
```

## Convenções

- Python 3.12+, tipagem em tudo, `ruff` para lint e formatação.
- Banco PostgreSQL, inclusive nos testes de integração.
- Nomes de domínio em português; infraestrutura pode ser em inglês.
- Datas de lançamento são `date`, sem hora. Fuso: `America/Sao_Paulo`.
- Mudança de schema só por migração Alembic.
- Segredos só em variáveis de ambiente. Logs sem senhas, tokens, dados pessoais ou valores.
- Commits pequenos, no padrão Conventional Commits (`feat:`, `fix:`, `test:`, `refactor:`).

## Como trabalhar comigo

- Antes de implementar algo grande, apresente um plano curto e espere confirmação.
- Se o pedido for ambíguo ou contrariar a constituição, pergunte em vez de supor.
- Ao terminar, rode os testes e o lint e diga o resultado.
- Não crie arquivos de documentação extras sem pedido.
