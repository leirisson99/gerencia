# Quickstart: Tipo de Renda e Ciclo Mensal do Prestador

## Pré-requisitos

```bash
cd backend
docker compose up -d db
uv sync
uv run alembic upgrade head
```

## Testes automatizados

```bash
uv run pytest tests/domain/test_ciclo.py tests/domain/test_usuario.py
uv run pytest tests/api/test_prestador.py tests/api/test_cadastro.py tests/api/test_perfil.py
uv run pytest            # suíte completa: fluxo CLT sem mudança (SC-002)
uv run ruff check . && uv run ruff format --check .
uv run alembic downgrade -1 && uv run alembic upgrade head   # migração reversível
```

## Validação manual (`/docs`)

1. Cadastrar com `"tipo_renda": "prestador"`; `GET /me` mostra `prestador`.
2. `POST /lancamentos` de uma saída hoje, sem salário → 201.
3. `GET /ciclos/atual` → dia 1 ao último dia do mês, `aberto: true`.
4. `POST /recorrencias` (aluguel, dia 10) → `GET /ciclos/{hoje}/lancamentos` mostra um previsto
   no dia 10; repetir `GET /ciclos/atual` não duplica.
5. `PATCH /me` com `"tipo_renda": "clt"` → 409 `lancamentos_sem_ciclo` (não há salário).
6. Cadastrar outra conta sem `tipo_renda` → `clt`; `POST /lancamentos` sem salário → 409
   `salario_necessario`, como antes.
