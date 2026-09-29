# Implementation Plan: Dívidas com Parcelas

**Branch**: `007-dividas` | **Date**: 2026-09-29 | **Spec**: [spec.md](spec.md)

## Summary

Tabela `divida` e colunas `lancamento.divida_id` / `parcela_num` (migração `0007`). Regras puras
em `domain/parcelas.py`: `dividir(valor_total, n)`, `datas_das_parcelas(dia, inicio, n)` (usa
`data_prevista` da 006) e `situacao(parcelas)`. `POST /api/v1/dividas` cria a dívida e as N
parcelas numa transação, passando pela mesma regra de cobertura dos lançamentos;
`GET /api/v1/dividas` e `GET /api/v1/dividas/{id}` mostram a situação. Pagar é editar a parcela.

## Technical Context

**Language/Version**: Python 3.14 · **Dependencies**: as mesmas

**Storage**: PostgreSQL 17 — `divida`; `lancamento.divida_id` (FK RESTRICT), `parcela_num`,
`UNIQUE (divida_id, parcela_num)`, CHECK de pareamento ([data-model.md](data-model.md))

**Testing**: `tests/domain/test_parcelas.py`, `tests/api/test_dividas.py`

**Project Type**: web service; escopo só do backend

## Constitution Check

| Princípio | Verificação | Status |
| --- | --- | --- |
| I. Integridade | Centavos `int`; soma das parcelas = total (teste); cartão → `conta_no_saldo = False`; dívida + parcelas numa transação. | ✅ |
| II. Ciclo | Parcelas passam pela cobertura (nada antes do primeiro salário). | ✅ |
| III. Teste primeiro | `dividir`, `datas_das_parcelas`, `situacao` puras e testadas antes. | ✅ |
| IV. Contratos | `DividaIn` com enums; `DividaOut` com situação e parcelas. | ✅ |
| V. Isolamento | Dívida e categoria de outro usuário → 404 (teste). | ✅ |
| VI. Escopo | Só cadastro, parcelas, marcação e situação; resumo de dívidas é P1. | ✅ |

**Resultado**: sem violações.

## Project Structure

```text
backend/
├── alembic/versions/0007_divida.py
├── app/domain/parcelas.py
├── app/models/divida.py            # + Lancamento.divida_id, parcela_num
├── app/schemas/divida.py           # + LancamentoOut.divida_id, parcela_num
├── app/services/divida.py
├── app/services/lancamento.py      # cobertura pública; parcela não exclui nem troca categoria
├── app/api/routes/dividas.py
└── tests/domain/test_parcelas.py, tests/api/test_dividas.py
```

## Complexity Tracking

Sem violações.
