# Quickstart: Ciclo Aberto pelo Salário

Guia para validar a feature 001 de ponta a ponta. Detalhes em
[data-model.md](data-model.md) e [contracts/api.md](contracts/api.md). Pré-requisitos e
subida do ambiente são os mesmos da
[002](../002-cadastro-login/quickstart.md).

## Migração, testes e lint

```bash
cd backend
uv run alembic upgrade head      # cria lancamento e as categorias iniciais
uv run pytest                    # domínio (tests/domain/test_ciclo.py) + API
uv run ruff check . && uv run ruff format --check .
uv run alembic downgrade -1 && uv run alembic upgrade head   # 0003 reversível
```

## Roteiro manual (API)

Com a API em `http://localhost:8000`, um usuário recém-cadastrado (cookie em `jar.txt`) e
`CT='Content-Type: application/json'`. Os exemplos usam datas passadas (jun–ago/2026); as datas da spec
(out–dez/2026) ficam para os testes, que usam relógio fixo.

1. **Categorias iniciais**: `GET /api/v1/categorias` → 8 categorias, "Salário" primeiro.
   Guarde os ids de "Salário" (`$SAL`), "Renda extra" (`$EXTRA`) e "Alimentação" (`$ALIM`).
2. **Bloqueio antes do salário (US2.1)**: `POST /lancamentos` com `$ALIM` → 409
   `salario_necessario`, mensagem "Lance seu salário para abrir o primeiro ciclo.".
   `GET /ciclos/atual` → 404 `sem_ciclo`.
3. **Lançar salário (US1.1)**: `POST /lancamentos`
   `{"valor":500000,"categoria_id":$SAL,"data":"2026-06-05"}` → 201, `abre_ciclo: true`.
   `GET /ciclos/atual` → `inicio 2026-06-05`, `fim null`, `anterior null`, `proximo null`.
4. **Data antes do primeiro ciclo (US2.2/2.3)**: gasto em `2026-06-01` → 409
   `antes_do_primeiro_ciclo`; gasto em `2026-06-05` → 201.
5. **Renda extra não abre ciclo (US1.3)**: entrada em `$EXTRA` com data `2026-06-20` → 201,
   `abre_ciclo: false`; `GET /ciclos/atual` continua desde `2026-06-05`.
6. **Segundo e terceiro salários (US1.2, US3)**: salários em `2026-07-06` e `2026-08-05`.
   `GET /ciclos/2026-07-20` → `2026-07-06` a `2026-08-04`, `anterior 2026-06-05`,
   `proximo 2026-08-05`. `GET /ciclos/2026-06-01` → 404 `sem_ciclo`.
7. **Salário futuro (US1.4)**: salário com data de amanhã → 422, `campos.data`.
8. **Corrigir data (US4.1)**: `PATCH` do salário de 06/07 para `2026-07-04` →
   `GET /ciclos/2026-06-05` termina em `2026-07-03`.
9. **Excluir salário do meio (US4.2)**: `DELETE` do salário de 04/07 → `GET /ciclos/2026-06-05`
   vai até `2026-08-04`.
10. **Recusa de exclusão (US4.3)**: com um único salário e outros lançamentos, `DELETE` dele →
    409 `lancamentos_sem_ciclo`; `PATCH` da data dele para depois de um gasto → mesmo 409.
11. **Lançamentos por ciclo**: `GET /ciclos/2026-06-05/lancamentos` lista só os lançamentos
    com data dentro do ciclo.
12. **Sugestão (FR-012)**: `GET /salarios/sugestao` → valor do salário mais recente.
13. **Isolamento (FR-013)**: com outro usuário, `GET/PATCH/DELETE /lancamentos/{id}` de um
    lançamento do primeiro → 404; `POST /lancamentos` com a categoria do primeiro → 404.

## Resultado esperado

Todos os passos respondem como descrito, `uv run pytest` passa e o `ruff` não aponta nada.
