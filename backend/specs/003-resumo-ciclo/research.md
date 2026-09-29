# Research: Resumo do Ciclo

## R1. Onde calcular

- **Decision**: somar em Python, na função pura `resumir(movimentos)` de `domain/saldo.py`, sobre
  os lançamentos do ciclo já carregados.
- **Rationale**: Princípio III (regra de saldo no domínio, testável sem banco). Um ciclo tem
  dezenas de lançamentos; somar em memória é trivial.
- **Alternatives considered**: `SUM ... GROUP BY` no SQL (regra fora do domínio, filtros de saldo
  duplicados entre consulta e testes).

## R2. Formato da resposta

- **Decision**: `ciclo` (o mesmo `CicloOut` da 001), `entradas`, `saidas`, `saldo`,
  `saidas_por_categoria` e `entradas_por_categoria`, cada item com `categoria_id`, `nome` e
  `total`; ordem por total decrescente e nome.
- **Rationale**: FR-003/FR-007; listas separadas evitam o cliente filtrar por tipo, e o `ciclo`
  embutido permite navegar sem outra chamada.

## R3. Tipo usado nas somas

- **Decision**: soma por `lancamento.tipo` (copiado da categoria na 001).
- **Rationale**: o tipo guardado no lançamento é a fonte da verdade do movimento; a 001 garante
  que ele acompanha a categoria.

## R4. Rota

- **Decision**: `GET /api/v1/ciclos/{data}/resumo`. Para o ciclo atual, o cliente usa o
  `inicio` de `GET /ciclos/atual`.
- **Rationale**: uma rota só, sem duplicar `/ciclos/atual/resumo` (Princípio VI).
