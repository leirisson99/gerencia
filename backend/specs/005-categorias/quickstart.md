# Quickstart: Categorias Editáveis

```bash
uv run alembic upgrade head       # 0005
uv run pytest tests/domain/test_categoria.py tests/api/test_categorias.py
uv run alembic downgrade -1 && uv run alembic upgrade head
```

1. `POST /api/v1/categorias {"nome":"Pets","tipo":"saida"}` → 201; repetir com "pets" → 409.
2. `PATCH /api/v1/categorias/{outros} {"nome":"Diversos"}` → 200; o resumo do ciclo usa "Diversos".
3. `PATCH /api/v1/categorias/{transporte} {"ativa":false}` → some de `GET /categorias`, aparece
   com `?incluir_inativas=true`; lançar nela → 422.
4. `PATCH` em "Salário" → 409 `categoria_do_sistema`.
