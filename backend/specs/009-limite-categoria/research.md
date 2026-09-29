# Research: Limite por Categoria

## Onde guardar o limite

- **Decision**: coluna `categoria.limite BIGINT NULL` com `CHECK (limite > 0)`.
- **Rationale**: um limite por categoria, sem histórico (FR-004); nulo = sem limite.
- **Alternatives**: tabela `limite_categoria` (desnecessária sem histórico por ciclo).

## Cálculo da situação sem float

- **Decision**: `ok` se `usado*100 < limite*80`; `atencao` se `usado <= limite`; senão
  `estourado`. Inteiros do Python não estouram.
- **Rationale**: exato nas fronteiras (SC-002) e coerente com o Princípio I.
- **Alternatives**: percentual com `round` (erra na fronteira de 80%).

## Como saber se a situação piorou

- **Decision**: no serviço, antes de alterar, somar o usado da categoria de destino no ciclo da
  nova data; depois do `flush`, somar de novo; `piorou(situacao(antes), situacao(depois))`. Ordem
  `ok < atencao < estourado`.
- **Rationale**: cobre criar, confirmar previsto, trocar categoria e trocar data de ciclo com uma
  regra só; a soma reusa `domain/saldo.py::resumir` (mesmo filtro do saldo, FR-005).
- **Alternatives**: calcular pela diferença de valores (frágil com troca de categoria e data).

## Formato do aviso

- **Decision**: `POST`/`PATCH /lancamentos` devolvem `LancamentoComAvisoOut` =
  `LancamentoOut` + `aviso_limite: AvisoLimiteOut | null`.
- **Rationale**: o aviso só existe na resposta da escrita (spec, Key Entities); `GET` não muda.
- **Alternatives**: cabeçalho HTTP (menos visível no OpenAPI); campo em todo `LancamentoOut`
  (sem sentido em leituras).

## Remover o limite no PATCH

- **Decision**: `limite: null` remove; ausência não muda. O serviço usa `model_fields_set`.
- **Rationale**: FR-003 (remover); exceção explícita à regra "sem null" das outras rotas.

## Limite em categoria de entrada

- **Decision**: `domain/limite.py::limite_permitido(tipo)`; o serviço responde 422 `validacao`
  com `campos.limite` ao criar ou editar.
- **Rationale**: regra de domínio fora do schema, testável isolada.
