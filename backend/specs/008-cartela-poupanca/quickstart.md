# Quickstart: Cartela de Poupança

```bash
uv run alembic upgrade head       # 0008
uv run pytest tests/domain/test_cartela.py tests/api/test_cartelas.py
uv run alembic downgrade -1 && uv run alembic upgrade head
```

1. `POST /cartelas {"nome":"Viagem","meta":100000}` → 44 casas + ajuste de 1000.
2. Salário lançado; `POST /cartelas/{id}/casas/{casa}/deposito` → casa depositada; o resumo do
   ciclo tem a saída em "Poupança".
3. `DELETE` do depósito → casa livre; a saída some.
