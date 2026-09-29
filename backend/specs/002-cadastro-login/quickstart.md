# Quickstart: Cadastro e Login

Guia para validar a feature 002 de ponta a ponta. Detalhes em
[data-model.md](data-model.md) e [contracts/api.md](contracts/api.md).

## Pré-requisitos

- Docker Desktop rodando.
- `uv` instalado (`powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`).
- Arquivo `backend/.env` a partir de `backend/.env.example`:
  `DATABASE_URL`, `TEST_DATABASE_URL`, `FRONTEND_ORIGIN`, `COOKIE_SECURE=false` em dev.

## Subir o ambiente

```bash
cd backend
docker compose up -d db          # PostgreSQL 17 com os bancos gerencia e gerencia_test
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

`GET http://localhost:8000/health` → `{"status": "ok"}`.

## Testes e lint

```bash
uv run pytest                    # domínio + API contra gerencia_test
uv run ruff check . && uv run ruff format --check .
uv run alembic downgrade base && uv run alembic upgrade head   # migração reversível
```

Esperado: tudo verde, sem avisos do ruff.

## Validação manual (http://localhost:8000/docs)

1. **Cadastro**: `POST /api/v1/auth/cadastro` com os dados do exemplo do contrato → 201 e
   cookie `sessao`. Repetir com `ANA@Exemplo.com` → 409 `email_ja_cadastrado`.
2. **Validações**: telefone `123`, senha `abcdefgh`, data de nascimento amanhã, nome `"   "`
   → 422 com o campo indicado em `campos`.
3. **Login**: sair (`POST /auth/logout` → 204), `GET /me` → 401. Entrar com a senha certa →
   200.
4. **Bloqueio**: 5 logins com senha errada → a 6ª tentativa, mesmo com a senha certa, dá 429
   com `Retry-After`. Repetir com um e-mail inexistente → mesmas respostas.
5. **Perfil**: `PATCH /me` com telefone novo → 200 com o valor normalizado. Com `email` no
   corpo → 422. Com `data_nascimento: null` → a data some.
6. **Troca de senha**: entrar em dois navegadores; trocar a senha no primeiro → 204; no
   segundo, `GET /me` → 401. Senha atual errada → 400.
7. **Troca obrigatória**: marcar `troca_senha_obrigatoria = true` no banco para o usuário;
   entrar → 200 com o flag; `GET /me` → 403; `PUT /me/senha` → 204; `GET /me` → 200.
8. **Categoria de sistema**: após o cadastro, existe uma categoria "Salário" (`entrada`,
   `sistema = true`) para o usuário.
