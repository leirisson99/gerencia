# Quickstart: Dívidas com Parcelas

```bash
uv run alembic upgrade head       # 0007
uv run pytest tests/domain/test_parcelas.py tests/api/test_dividas.py
uv run alembic downgrade -1 && uv run alembic upgrade head
```

1. Salário em `2026-06-05`; `POST /dividas` Notebook 100000 em 3, dia 15 → parcelas 33333,
   33333, 33334 em 15/06, 15/07, 15/08.
2. `PATCH /lancamentos/{parcela 1} {"status":"realizado"}` → `GET /dividas/{id}` mostra 1 de 3.
3. Dívida no cartão → parcelas com `conta_no_saldo: false`.
