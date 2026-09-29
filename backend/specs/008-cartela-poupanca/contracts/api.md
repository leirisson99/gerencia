# Contrato: Cartela de Poupança

## `POST /api/v1/cartelas` → 201 `CartelaOut`

`{"nome": "Viagem", "meta": 100000, "valor_base": 100}` (`valor_base` opcional, padrão 100).
Erros: 422 `validacao` (inclusive `meta` < base e mais de 1.000 casas).

## `GET /api/v1/cartelas` → 200 `CartelaOut[]` · `GET /api/v1/cartelas/{id}` → 200 `CartelaOut`

```json
{
  "id": 1, "nome": "Viagem", "meta": 100000, "valor_base": 100,
  "guardado": 5400, "falta": 94600, "percentual": 5, "maior_casa_livre": 4300,
  "casas": [
    { "id": 10, "ordem": 1, "valor": 100, "is_ajuste": false, "depositado_em": null, "lancamento_id": null }
  ]
}
```

## `POST /api/v1/cartelas/{id}/casas/{casa_id}/deposito` → 200 `CartelaOut`

Marca a casa (data de hoje) e cria a saída em "Poupança". Erros: 409 `casa_depositada`;
409 `salario_necessario` / `antes_do_primeiro_ciclo`; 404.

## `DELETE /api/v1/cartelas/{id}/casas/{casa_id}/deposito` → 200 `CartelaOut`

Desmarca e remove o lançamento. Erros: 409 `casa_livre`; 404.

## Lançamento de depósito

`DELETE /lancamentos/{id}` → 409 `deposito_de_cartela`; `PATCH` com `valor`, `status` ou
`categoria_id` → 422.

## Categorias

"Poupança" aparece em `GET /categorias` como `sistema: true`; renomear ou desativar →
409 `categoria_do_sistema`.
