# Contrato: Categorias Editáveis

**CategoriaOut** passa a ter `ativa`:

```json
{ "id": 7, "nome": "Pets", "tipo": "saida", "sistema": false, "ativa": true }
```

## `GET /api/v1/categorias?incluir_inativas=true` → 200 `CategoriaOut[]`

Sem o parâmetro: só ativas. Com ele: todas. Ordem: "Salário", entradas e saídas por nome.

## `POST /api/v1/categorias` → 201 `CategoriaOut`

`{"nome": "Pets", "tipo": "saida"}`. Erros: 422 `validacao`; 409 `categoria_existente`.

## `PATCH /api/v1/categorias/{id}` → 200 `CategoriaOut`

`{"nome": "Diversos"}` e/ou `{"ativa": false}`. `tipo` e campos extras → 422; `null` → 422.
Erros: 404 `nao_encontrado`; 409 `categoria_existente`; 409 `categoria_do_sistema`.
