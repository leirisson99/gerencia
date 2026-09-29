# Contrato: Limite por Categoria

Mesmas regras das features anteriores (cookie `sessao`, formato único de erro). Valores em
centavos, inteiros. Todas as mudanças são aditivas.

## Categorias

**CategoriaOut** ganha `limite` (`null` sem limite):

```json
{ "id": 12, "nome": "Lazer", "tipo": "saida", "sistema": false, "ativa": true, "limite": 30000 }
```

- `POST /api/v1/categorias`: `{"nome": "Pets", "tipo": "saida", "limite": 20000}`; `limite`
  opcional.
- `PATCH /api/v1/categorias/{id}`: `{"limite": 40000}` define ou muda; `{"limite": null}`
  remove; ausente não muda.
- Erros: 422 `validacao` com `campos.limite` para limite em categoria de entrada, zero,
  negativo ou não inteiro. Categorias do sistema ("Salário", "Poupança") aceitam limite se forem
  de saída (só nome e ativação são protegidos).

## Resumo do ciclo

`GET /api/v1/ciclos/{data}/resumo`: itens de `saidas_por_categoria` ganham `limite` e
`situacao` (`"ok" | "atencao" | "estourado"`; ambos `null` sem limite). Itens de
`entradas_por_categoria` têm os dois sempre `null`.

```json
{ "categoria_id": 12, "nome": "Lazer", "total": 25000, "limite": 30000, "situacao": "atencao" }
```

Categoria ativa de saída com limite e sem gasto no ciclo aparece com `total: 0` e situação
`"ok"`, depois das que têm gasto.

## Lançamentos

`POST /api/v1/lancamentos` e `PATCH /api/v1/lancamentos/{id}` respondem `LancamentoOut` +
`aviso_limite`:

```json
{
  "id": 42, "...": "demais campos de LancamentoOut",
  "aviso_limite": {
    "categoria_id": 12, "nome": "Lazer", "usado": 25000, "limite": 30000, "situacao": "atencao"
  }
}
```

`aviso_limite` é `null` quando a situação da categoria, no ciclo da data do lançamento, não
piorou. O limite nunca recusa um lançamento. `GET` e `DELETE` não mudam. O depósito de cartela
(`POST /cartelas/.../deposito`) não traz aviso.
