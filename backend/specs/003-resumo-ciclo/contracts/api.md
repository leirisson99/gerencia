# Contrato da API: Resumo do Ciclo

Mesmas regras da 001/002 (cookie `sessao`, formato único de erro). Valores em centavos.

## `GET /api/v1/ciclos/{data}/resumo` → 200 `ResumoCicloOut`

```json
{
  "ciclo": {
    "inicio": "2026-10-05",
    "fim": "2026-11-05",
    "aberto": false,
    "anterior": null,
    "proximo": "2026-11-06"
  },
  "entradas": 530000,
  "saidas": 230000,
  "saldo": 300000,
  "saidas_por_categoria": [
    { "categoria_id": 12, "nome": "Moradia", "total": 150000 },
    { "categoria_id": 13, "nome": "Alimentação", "total": 80000 }
  ],
  "entradas_por_categoria": [
    { "categoria_id": 10, "nome": "Salário", "total": 500000 },
    { "categoria_id": 11, "nome": "Renda extra", "total": 30000 }
  ]
}
```

- Só lançamentos `realizado` com `conta_no_saldo = true`.
- Listas ordenadas por `total` decrescente e, no empate, por `nome`.
- Erros: 404 `sem_ciclo` (data sem ciclo); 422 data inválida; 401/403 como na 002.
