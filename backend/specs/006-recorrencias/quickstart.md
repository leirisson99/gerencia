# Quickstart: Recorrências

```bash
uv run alembic upgrade head       # 0006
uv run pytest tests/domain/test_recorrencia.py tests/api/test_recorrencias.py
uv run alembic downgrade -1 && uv run alembic upgrade head
```

1. Salário em `2026-06-05`; `POST /recorrencias` "Internet" dia 10 → previsto em `2026-06-10`.
2. `POST /recorrencias` "Aluguel" dia 1 → previsto em `2026-07-01`.
3. Salário em `2026-07-06` → previstos em `2026-07-10` e `2026-08-01`.
4. `PATCH /lancamentos/{previsto} {"status":"realizado"}` → o resumo conta o valor.
