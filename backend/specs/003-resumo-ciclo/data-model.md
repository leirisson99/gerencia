# Data Model: Resumo do Ciclo

Sem mudança de schema e sem migração. O resumo é derivado dos lançamentos do ciclo
(tabela `lancamento` da 001) a cada consulta.

`app/domain/saldo.py`:

```text
Movimento(categoria_id: int, tipo: "entrada" | "saida", valor: int, status: str, conta_no_saldo: bool)
Resumo(entradas: int, saidas: int, saldo: int, por_categoria: dict[int, int])
resumir(movimentos) -> Resumo
```

Regras:

- Conta só `status = realizado` e `conta_no_saldo = True`.
- `saldo = entradas − saidas` (pode ser negativo).
- `por_categoria` só tem categorias com total > 0; a soma das entradas por categoria é
  `entradas` e a das saídas é `saidas`.
