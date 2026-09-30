# gerencia

Controle financeiro pessoal organizado em torno do **ciclo do salário**. O sistema responde a três perguntas: quanto entrou, para onde foi (por categoria) e quanto sobrou. O que sobra alimenta **cartelas de poupança** por meta.

- Multiusuário: qualquer pessoa se cadastra com e-mail e senha, e cada uma vê só os próprios dados.
- Lançamentos manuais ou importados de extrato de conta (OFX, CSV ou PDF), sempre com prévia confirmada pelo usuário.
- Um único administrador, que só pode resetar senhas.

## Funcionalidades

| Recurso | O que faz |
| --- | --- |
| Ciclo do salário | Cada salário lançado abre um ciclo, que vai até a véspera do próximo |
| Resumo e projeção | Saldo do ciclo, gasto por categoria e projeção com os previstos |
| Categorias e limites | Categorias de entrada e saída, com limite de gasto por ciclo |
| Recorrências | Gastos e rendas fixas que geram um lançamento previsto por ciclo |
| Dívidas | `devo` ou `me_devem`, divididas em parcelas previstas |
| Cartelas de poupança | Meta dividida em casas sequenciais; depositar numa casa não sai do saldo do ciclo |
| Importação de extrato | Lê OFX, CSV ou PDF, mostra uma prévia e só grava as linhas confirmadas |
| Calendário | Lançamentos do ciclo organizados por dia |
| Painel do administrador | Lista as contas e reseta senhas |

## Stack

| Parte | Tecnologias |
| --- | --- |
| [backend/](backend/) | Python 3.12, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL 17, uv, pytest, ruff |
| [frontend/](frontend/) | Next.js 16, React 19, TypeScript, Tailwind CSS 4, shadcn/ui, react-hook-form, zod |

Valores em dinheiro são sempre inteiros em centavos, do banco ao JSON da API.

## Como rodar

Pré-requisitos: Docker Desktop, [uv](https://docs.astral.sh/uv/) e Node.js.

### Backend

```bash
cd backend
cp .env.example .env
docker compose up -d db              # PostgreSQL com os bancos gerencia e gerencia_test
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload # http://localhost:8000
```

Para criar o administrador (só existe um):

```bash
uv run python -m app.cli criar-admin --nome ... --email ... --telefone ... --cargo ...
```

### Frontend

```bash
cd frontend
cp .env.example .env.local           # API_URL aponta para o backend
npm install
npm run dev                          # http://localhost:3000
```

O Next reescreve as chamadas `/api/v1/*` para o backend definido em `API_URL`.

## Testes e lint

```bash
# backend/
uv run pytest
uv run ruff check . && uv run ruff format .

# frontend/
npm run lint
```

## Documentação

- [backend/.specify/memory/constitution.md](backend/.specify/memory/constitution.md): regras do projeto (fonte da verdade).
- [backend/specs/](backend/specs/): especificação de cada feature, de `001-ciclo-salario` a `011-importacao-extrato`.
- [backend/CLAUDE.md](backend/CLAUDE.md): glossário do domínio, modelo de dados e regras de cálculo.
