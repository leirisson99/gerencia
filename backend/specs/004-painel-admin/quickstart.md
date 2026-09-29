# Quickstart: Painel do Administrador

```bash
uv run alembic upgrade head        # 0004
uv run pytest tests/domain/test_senha_temporaria.py tests/services tests/api/test_admin.py
uv run alembic downgrade -1 && uv run alembic upgrade head
```

Roteiro manual:

1. `uv run python -m app.cli criar-admin ...` → senha temporária exibida. Rodar de novo → recusa.
2. Entrar como admin → `troca_senha_obrigatoria: true`; `PUT /api/v1/me/senha`.
3. Cadastrar a Ana (outro cliente). Admin: `GET /api/v1/admin/usuarios?busca=ana` → só nome,
   e-mail e criação.
4. Admin: `POST /api/v1/admin/usuarios/{ana}/reset-senha` → senha temporária; a sessão da Ana
   passa a responder 401; a Ana entra com a temporária e precisa trocá-la.
5. Ana tentando `GET /api/v1/admin/usuarios` → 403 `acesso_negado`.
6. `SELECT * FROM acao_admin` → registro do reset.
