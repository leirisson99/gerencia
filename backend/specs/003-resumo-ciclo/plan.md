# Implementation Plan: Resumo do Ciclo

**Branch**: `003-resumo-ciclo` | **Date**: 2026-09-28 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/003-resumo-ciclo/spec.md`

## Summary

Nova rota `GET /api/v1/ciclos/{data}/resumo` com entradas, saídas, saldo e totais por categoria
do ciclo que contém a data. O cálculo é uma função pura em `app/domain/saldo.py` sobre os
lançamentos do ciclo (já obtidos por `services/ciclo.lancamentos_do_ciclo`); nada é guardado e
não há mudança de schema. Decisões em [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.14

**Primary Dependencies**: as mesmas da 001/002; nenhuma nova

**Storage**: PostgreSQL 17, sem mudança de schema ([data-model.md](data-model.md))

**Testing**: pytest — `tests/domain/test_saldo.py` e `tests/api/test_resumo.py`

**Target Platform**: servidor Linux (container) atrás de HTTPS

**Project Type**: web service (API HTTP); escopo só do backend

**Performance Goals**: < 1 s por resumo; um ciclo tem dezenas de lançamentos

**Constraints**: centavos `int`; só `realizado` e `conta_no_saldo`; isolamento por usuário

**Scale/Scope**: 1 rota, 1 módulo de domínio, 1 serviço

## Constitution Check

| Princípio | Verificação | Status |
| --- | --- | --- |
| I. Integridade Financeira | Saldo = entradas − saídas só com `realizado` e `conta_no_saldo`; derivado, nunca guardado; somas por categoria fecham com os totais (teste). | ✅ |
| II. Ciclo Aberto pelo Salário | Usa o ciclo derivado da 001; nada de ciclo guardado. | ✅ |
| III. Domínio Puro e Teste Primeiro | `resumir` pura em `domain/saldo.py`, testes antes (previsto, fora do saldo, negativo, vazio, somas). | ✅ |
| IV. API com Contratos Tipados | `ResumoCicloOut` tipado; 404 `sem_ciclo` no formato único. | ✅ |
| V. Contas e Isolamento | Só lançamentos do usuário da sessão (teste com outro usuário). | ✅ |
| VI. Escopo P0 | Só saldo e gasto por categoria; percentuais e comparação ficam fora. | ✅ |

**Resultado**: sem violações.

## Project Structure

```text
specs/003-resumo-ciclo/
├── spec.md, plan.md, research.md, data-model.md, quickstart.md, tasks.md
└── contracts/api.md

backend/
├── app/domain/saldo.py          # Movimento, TotalCategoria, Resumo, resumir
├── app/schemas/resumo.py        # ResumoCicloOut, TotalCategoriaOut
├── app/services/resumo.py       # resumo_do_ciclo (busca, chama o domínio, nomeia e ordena)
├── app/api/routes/ciclos.py     # + GET /ciclos/{data}/resumo
└── tests/domain/test_saldo.py, tests/api/test_resumo.py
```

**Structure Decision**: segue a 001; a rota fica junto das demais de ciclo.

## Complexity Tracking

Sem violações.
