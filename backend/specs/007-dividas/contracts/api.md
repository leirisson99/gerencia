# Contrato: Dívidas com Parcelas

## `POST /api/v1/dividas` → 201 `DividaOut`

```json
{
  "descricao": "Notebook", "pessoa": "Loja X", "direcao": "devo", "valor_total": 100000,
  "parcelas": 3, "forma_pagamento": "pix", "dia_vencimento": 15, "data_inicio": "2026-10-05",
  "categoria_id": 12
}
```

Erros: 422 `validacao`; 404 `nao_encontrado` (categoria); 409 `salario_necessario` /
`antes_do_primeiro_ciclo`.

## `GET /api/v1/dividas` → 200 `DividaOut[]` · `GET /api/v1/dividas/{id}` → 200 `DividaOut`

```json
{
  "id": 1, "descricao": "Notebook", "pessoa": "Loja X", "direcao": "devo",
  "valor_total": 100000, "parcelas": 3, "forma_pagamento": "pix", "dia_vencimento": 15,
  "data_inicio": "2026-10-05", "categoria_id": 12,
  "parcelas_pagas": 1, "valor_pago": 33333, "valor_restante": 66667, "quitada": false,
  "lancamentos": [ { "...": "LancamentoOut", "divida_id": 1, "parcela_num": 1 } ]
}
```

`LancamentoOut` ganha `divida_id` e `parcela_num`.

## Pagar/receber

`PATCH /api/v1/lancamentos/{parcela}` `{"status": "realizado"}`. Mudar `categoria_id` de parcela
→ 422; `DELETE` de parcela → 409 `parcela_de_divida`.
