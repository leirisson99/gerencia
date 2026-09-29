# Contrato: Recorrências

**RecorrenciaOut**

```json
{ "id": 3, "descricao": "Internet", "valor": 10000, "tipo": "saida", "categoria_id": 12, "dia": 10, "ativa": true }
```

**LancamentoOut** ganha `recorrencia_id` (null em lançamentos manuais).

## `GET /api/v1/recorrencias` → 200 `RecorrenciaOut[]`

Todas do usuário (ativas e inativas), por dia e descrição.

## `POST /api/v1/recorrencias` → 201 `RecorrenciaOut`

`{"descricao": "Internet", "valor": 10000, "categoria_id": 12, "dia": 10}`. Gera o previsto do
ciclo aberto, se houver. Erros: 422 `validacao` (inclusive `categoria_id` "Salário" ou inativa);
404 `nao_encontrado` (categoria).

## `PATCH /api/v1/recorrencias/{id}` → 200 `RecorrenciaOut`

Campos opcionais `descricao`, `valor`, `categoria_id`, `dia`, `ativa` (sem `null`). Vale para os
próximos ciclos. Erros: 404; 422.

## Confirmar pagamento

`PATCH /api/v1/lancamentos/{id}` com `{"status": "realizado"}` (e `valor`/`data` se mudaram).
