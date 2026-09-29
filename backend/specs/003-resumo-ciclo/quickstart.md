# Quickstart: Resumo do Ciclo

Ambiente e cadastro como na [002](../002-cadastro-login/quickstart.md); lançamentos como na
[001](../001-ciclo-salario/quickstart.md). Sem migração nova.

```bash
uv run pytest tests/domain/test_saldo.py tests/api/test_resumo.py
```

Roteiro manual:

1. Lançar salário de 500000 em `2026-06-05`, renda extra de 30000, gastos de 80000
   (Alimentação) e 150000 (Moradia) no mesmo ciclo.
2. `GET /api/v1/ciclos/2026-06-05/resumo` → entradas 530000, saídas 230000, saldo 300000;
   saídas: Moradia antes de Alimentação.
3. Lançar um gasto `previsto` → o resumo não muda.
4. `GET /api/v1/ciclos/2026-06-01/resumo` → 404 `sem_ciclo`.
