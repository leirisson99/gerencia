# Quickstart: Limite por Categoria

```bash
uv run alembic upgrade head       # 0009
uv run pytest tests/domain/test_limite.py tests/api/test_limite.py
uv run alembic downgrade -1 && uv run alembic upgrade head
```

Com salário lançado e a categoria "Lazer" (saída):

1. `PATCH /categorias/{lazer} {"limite": 30000}` → `limite: 30000`; em "Renda extra" → 422
   `campos.limite`.
2. `GET /ciclos/{data}/resumo` → Lazer com `total: 0`, `situacao: "ok"`.
3. Lançar R$ 250 em Lazer → `aviso_limite.situacao == "atencao"`; mais R$ 10 → `null`; mais
   R$ 50 → `"estourado"` (usado 31000). Todos aceitos (201).
4. Lançar previsto de R$ 100 → sem aviso; confirmar com `PATCH {"status": "realizado"}` → aviso
   se piorar.
5. `PATCH /categorias/{lazer} {"limite": null}` → resumo sem limite nem situação.

Frontend: categorias mostram e editam o limite; o dashboard mostra o medidor com a situação em
ícone e texto; lançar ou confirmar um gasto que piora a situação mostra um aviso.
