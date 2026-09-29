# Implementation Plan: Categorias Editáveis

**Branch**: `005-categorias` | **Date**: 2026-09-29 | **Spec**: [spec.md](spec.md)

## Summary

`POST /api/v1/categorias` e `PATCH /api/v1/categorias/{id}` (nome, ativa) e o parâmetro
`incluir_inativas` em `GET /categorias`, que passa a devolver `ativa`. Unicidade de nome por
usuário garantida por índice único em `(usuario_id, lower(nome))` (migração `0005`). A regra
"categoria do sistema não muda" fica em `domain/categoria.py`.

## Technical Context

**Language/Version**: Python 3.14 · **Dependencies**: as mesmas

**Storage**: PostgreSQL 17 — índice `uq_categoria_usuario_nome` (migração `0005`)

**Testing**: `tests/domain/test_categoria.py`, `tests/api/test_categorias.py`

**Project Type**: web service; escopo só do backend

## Constitution Check

| Princípio | Verificação | Status |
| --- | --- | --- |
| II. Ciclo | "Salário" (única que abre ciclo) protegida contra renomear e desativar. | ✅ |
| III. Teste primeiro | Regra de edição em `domain/categoria.py` testada antes; API testada. | ✅ |
| IV. Contratos | `CategoriaIn`, `CategoriaPatch` com `extra="forbid"`; tipo não editável. | ✅ |
| V. Isolamento | Categoria de outro usuário → 404 (teste). | ✅ |
| VI. Escopo | Sem exclusão nem limites; só criar, renomear, desativar. | ✅ |

**Resultado**: sem violações.

## Project Structure

```text
backend/
├── alembic/versions/0005_categoria_nome_unico.py
├── app/domain/categoria.py        # + verificar_edicao
├── app/schemas/categoria.py       # + CategoriaIn, CategoriaPatch; CategoriaOut.ativa
├── app/services/categoria.py      # + criar_categoria, editar_categoria
├── app/api/routes/categorias.py   # + POST, PATCH, incluir_inativas
└── tests/domain/test_categoria.py, tests/api/test_categorias.py
```

## Decisões

- **Unicidade**: índice funcional `lower(nome)`; o nome é gravado sem espaços nas pontas.
  `IntegrityError` vira 409 `categoria_existente` (cobre requisições simultâneas).
- **Sistema**: renomear ou desativar "Salário" → 409 `categoria_do_sistema`.
- **Tipo**: não aceito no PATCH (campo extra → 422).
- **Inativa**: a checagem em lançamentos já existe (001); reativar é `PATCH {"ativa": true}`.

## Complexity Tracking

Sem violações.
