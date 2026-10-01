# Quickstart: Serviços a Receber

## Pré-requisitos

```bash
cd backend
docker compose up -d db
uv sync
uv run alembic upgrade head
```

## Testes automatizados

```bash
uv run pytest tests/domain/test_servico.py tests/domain/test_ciclo.py
uv run pytest tests/api/test_servicos.py tests/api/test_isolamento.py
uv run pytest
uv run ruff check . && uv run ruff format --check .
uv run alembic downgrade -1 && uv run alembic upgrade head
```

## Validação manual (`/docs`)

1. Cadastrar com `"tipo_renda": "prestador"`.
2. `POST /servicos` (Loja da Maria, 80000, data prevista daqui a 5 dias, "Renda extra") → 201,
   `situacao: "a_receber"`; `GET /ciclos/{data}/lancamentos` mostra o previsto com `servico_id`.
3. `POST /servicos/{id}/recebimento` com `{"data": hoje, "valor": 75000}` → `recebido`; o
   resumo do mês mostra entradas de 75000.
4. `DELETE /servicos/{id}/recebimento` → volta a `a_receber`; o resumo volta ao anterior.
5. `PATCH /lancamentos/{lancamento_id}` com `{"valor": 1}` → 422.
6. `PATCH /me` com `{"tipo_renda": "clt"}` → 409 `servicos_pendentes`.
7. Conta `clt`: `GET /servicos` → 403 `perfil_sem_servicos`.
