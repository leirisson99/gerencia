# Implementation Plan: Cartela de Poupança

**Branch**: `008-cartela-poupanca` | **Date**: 2026-09-29 | **Spec**: [spec.md](spec.md)

## Summary

Tabelas `cartela` e `casa` e a categoria de sistema "Poupança" para todos (migração `0008`;
cadastro passa a criá-la). Regras puras em `domain/cartela.py`: `gerar_casas(meta, base)` e
`progresso(casas, meta)`. Rotas: `POST/GET /api/v1/cartelas`, `GET /api/v1/cartelas/{id}`,
`POST` e `DELETE /api/v1/cartelas/{id}/casas/{casa_id}/deposito`. O depósito cria um lançamento
pela regra de cobertura dos lançamentos; lançamentos de depósito ficam protegidos. A proteção de
categoria passa de "Salário" para qualquer categoria do sistema.

## Technical Context

**Language/Version**: Python 3.14 · **Dependencies**: as mesmas

**Storage**: PostgreSQL 17 — `cartela`, `casa` (UNIQUE `(cartela_id, ordem)`, UNIQUE
`lancamento_id`, CHECK de pareamento depositado/lançamento) ([data-model.md](data-model.md))

**Testing**: `tests/domain/test_cartela.py`, `tests/api/test_cartelas.py`

**Project Type**: web service; escopo só do backend

## Constitution Check

| Princípio | Verificação | Status |
| --- | --- | --- |
| I. Integridade | N pela fórmula; casa de ajuste; soma = meta (teste); depósito gera saída em "Poupança"; depósito + marcação numa transação. | ✅ |
| II. Ciclo | Depósito é lançamento comum: passa pela cobertura (precisa de salário). | ✅ |
| III. Teste primeiro | `gerar_casas` e `progresso` puras, com os exemplos do briefing, testadas antes. | ✅ |
| IV. Contratos | `CartelaIn/Out`, `CasaOut` tipados. | ✅ |
| V. Isolamento | Cartela de outro usuário → 404 (teste). | ✅ |
| VI. Escopo | Só criar, gerar, marcar, ver progresso; sem prazo nem exclusão. | ✅ |

**Resultado**: sem violações.

## Project Structure

```text
backend/
├── alembic/versions/0008_cartela.py
├── app/domain/cartela.py
├── app/domain/categoria.py         # + Poupança nas iniciais; proteção para categorias do sistema
├── app/models/cartela.py
├── app/schemas/cartela.py
├── app/services/cartela.py
├── app/services/lancamento.py      # depósito não é excluído nem muda valor/status/categoria
├── app/api/routes/cartelas.py
└── tests/domain/test_cartela.py, tests/api/test_cartelas.py
```

## Complexity Tracking

Sem violações.
