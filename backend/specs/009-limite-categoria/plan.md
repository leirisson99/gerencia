# Implementation Plan: Limite por Categoria

**Branch**: `009-limite-categoria` | **Date**: 2026-09-29 | **Spec**: [spec.md](spec.md)

## Summary

Coluna opcional `categoria.limite` (centavos, só saída), editável em `POST`/`PATCH /categorias`.
O resumo do ciclo passa a trazer `limite` e `situacao` em `saidas_por_categoria`, incluindo
categorias ativas com limite e sem gasto (total 0). `POST`/`PATCH /lancamentos` respondem com
`aviso_limite` quando a situação da categoria piora no ciclo da data do lançamento. A situação e
a regra de "piorou" são funções puras em `domain/limite.py`, em aritmética inteira. O frontend
(Next, em `frontend/`) ganha o campo de limite nas categorias, o medidor no dashboard e o aviso
ao lançar.

## Technical Context

**Language/Version**: Python 3.14 (backend) · TypeScript/Next 16 (frontend)

**Primary Dependencies**: as mesmas (FastAPI, SQLAlchemy, Pydantic; Next, shadcn)

**Storage**: PostgreSQL 17 — coluna `categoria.limite BIGINT NULL`, `CHECK (limite > 0)`
(migração `0009`)

**Testing**: `tests/domain/test_limite.py`, `tests/api/test_limite.py`; ajustes em
`tests/api/test_categorias.py` e `tests/api/test_resumo.py`

**Project Type**: web service + frontend web

**Performance Goals**: resumo com limites < 1 s (SC-005); o aviso recalcula só a categoria de
destino no ciclo da data (uma consulta extra por escrita)

## Constitution Check

| Princípio | Verificação | Status |
| --- | --- | --- |
| I. Integridade financeira | Limite e usado em centavos `int`; situação por comparação inteira (`usado*100 < limite*80`), sem float. Usado segue o filtro do saldo (realizado e `conta_no_saldo`), então cartão não conta duas vezes. | ✅ |
| II. Ciclo | Situação calculada no ciclo derivado da data; nada de ciclo guardado. Limite sem histórico por ciclo. | ✅ |
| III. Teste primeiro | `situacao`, `piorou` e `limite_permitido` em `domain/limite.py`, testadas antes, com fronteiras 79,99% / 80% / 100% / 100,01% e limite de 1 centavo. | ✅ |
| IV. Contratos | Schemas tipados; `aviso_limite` só em POST/PATCH de lançamento (`LancamentoComAvisoOut`); mudanças aditivas, registradas no contrato. `limite: null` no PATCH remove (exceção documentada). | ✅ |
| V. Isolamento | Limite de categoria de outro usuário → 404 (teste). | ✅ |
| VI. Escopo | P2 com pedido explícito do usuário (spec, Assumptions). Sem limite total do ciclo, sem histórico, sem notificação. | ✅ |

**Resultado**: sem violações. Reavaliado após o desenho: sem mudanças.

## Project Structure

### Documentation

```text
specs/009-limite-categoria/
├── plan.md, research.md, data-model.md, quickstart.md
├── contracts/api.md
└── tasks.md            # /speckit-tasks
```

### Source Code

```text
backend/
├── alembic/versions/0009_limite_categoria.py
├── app/domain/limite.py            # situacao, piorou, limite_permitido
├── app/models/categoria.py         # + limite
├── app/schemas/categoria.py        # + limite em In/Patch/Out
├── app/schemas/resumo.py           # TotalCategoriaOut + limite, situacao
├── app/schemas/lancamento.py       # + AvisoLimiteOut, LancamentoComAvisoOut
├── app/services/categoria.py       # valida limite só em saída; PATCH distingue ausente de null
├── app/services/resumo.py          # limite/situação; categorias com limite sem gasto
├── app/services/limite.py          # usado no ciclo e aviso (antes/depois)
├── app/services/lancamento.py      # criar/editar devolvem o aviso
├── app/api/routes/lancamentos.py   # POST/PATCH → LancamentoComAvisoOut
└── tests/domain/test_limite.py, tests/api/test_limite.py

frontend/
├── lib/api/types.ts                # limite, situacao, AvisoLimite
├── features/categorias/            # campo "Limite por ciclo"
├── features/resumo/totais-por-categoria.tsx   # medidor e situação com ícone + texto
└── features/lancamentos/           # toast de aviso ao criar, editar e confirmar
```

**Structure Decision**: monólito FastAPI em `backend/` e Next em `frontend/`, como nas features
anteriores; a regra nova fica em `domain/`, e `services/` só consulta e chama o domínio.

## Decisões

Detalhes e alternativas em [research.md](research.md).

- **Situação**: `ok` se `usado*100 < limite*80`; `atencao` se `usado <= limite`; senão
  `estourado`.
- **Aviso**: calcula o usado da categoria de destino no ciclo da nova data antes e depois da
  mudança, na mesma transação; avisa só se `piorou`. Previsto, entrada e lançamento que não
  conta no saldo nunca avisam. Excluir não avisa.
- **Resumo**: categorias ativas de saída com limite e sem gasto entram com total 0, depois das
  que têm gasto (ordem total desc, nome); somas continuam fechando (FR-009).
- **Depósito de cartela**: não recebe aviso nesta versão (a rota é de cartela, não de
  lançamento); o gasto em "Poupança" conta no resumo normalmente.

## Complexity Tracking

Sem violações.
