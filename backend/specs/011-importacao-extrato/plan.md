# Implementation Plan: Importação de Extrato

**Branch**: `011-importacao-extrato` | **Date**: 2026-09-29 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/011-importacao-extrato/spec.md`

## Summary

O usuário escolhe o banco e o formato (OFX, CSV ou PDF), envia o extrato e recebe uma prévia com
as linhas classificadas (nova, já importada, possível duplicada, antes do primeiro ciclo,
inválida) e a categoria sugerida pelo histórico. Na confirmação, as linhas escolhidas viram
lançamentos realizados numa transação única, com as mesmas regras do lançamento manual, e os
salários do lote abrem ciclos. Leitores de extrato puros por banco e formato em
`app/domain/extrato/`; `pdfplumber` só na borda (`services/pdf.py`). Um `id_externo` por
lançamento importado impede duplicar. O frontend ganha a tela "Importar extrato". Decisões em
[research.md](research.md).

## Technical Context

**Language/Version**: Python 3.14 (backend) · TypeScript / Next 16 (frontend)

**Primary Dependencies**: as mesmas, mais `pdfplumber` (MIT) para extrair texto e posição dos
PDFs. OFX e CSV com parser próprio e a biblioteca padrão.

**Storage**: PostgreSQL 17 — coluna `lancamento.id_externo VARCHAR(120) NULL` + índice único
parcial `(usuario_id, id_externo)` (migração `0010_importacao`)

**Testing**: `tests/domain/test_extrato_valores.py`, `test_extrato_ofx.py`,
`test_extrato_csv.py`, `test_extrato_pdf.py`, `test_importacao.py` com fixtures **sintéticas**
em `tests/domain/fixtures/extratos/`; `tests/api/test_importacao.py` contra PostgreSQL

**Target Platform**: servidor Linux (container); navegador (frontend)

**Project Type**: web service + frontend web

**Performance Goals**: prévia de 200 linhas em menos de 3 s (SC-001); confirmação numa transação,
com uma consulta de cobertura para o lote inteiro

**Constraints**: arquivo de até 2 MB e 5.000 linhas; nunca `float` para valores; extratos reais
nunca versionados (`extratos/` no `.gitignore`)

**Scale/Scope**: 5 bancos + genérico, 3 formatos, 3 rotas

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Verificação | Status |
| --- | --- | --- |
| I. Integridade financeira | Texto → centavos só com dígitos em `int`, sem float nem Decimal (R5). Nada conta duas vezes: `id_externo` único e "possível duplicada". Extrato de fatura não é oferecido. Lote gravado numa transação só. | ✅ |
| II. Ciclo | Salário confirmado abre ciclo com as mesmas regras (data não futura, cobertura sobre o lote). Previstos só para o novo ciclo aberto. Nada de ciclo guardado. | ✅ |
| III. Teste primeiro | Leitores (OFX, CSV, PDF por banco), `centavos`, datas, `classificar`, `sugerir`, `id_externo` e cobertura do lote são puros e testados antes, com fixtures sintéticas. `pdfplumber` fica fora do domínio. | ✅ |
| IV. Contratos | Schemas Pydantic de entrada e saída, `extra="forbid"`, erros no formato único, novos códigos no contrato. `LancamentoOut.importado` é aditivo. | ✅ |
| V. Isolamento | Prévia, sugestão, "já importada" e confirmação só com dados do usuário. Categoria de outro usuário numa linha → 404 (teste). Extratos e descrições nunca vão para log. | ✅ |
| VI. Escopo | Importação permitida pela emenda 4.1.0 (prévia confirmada, sem IA, sugestão por regra fixa). P2 com pedido explícito. Sem Open Finance, OCR ou importação de fatura. | ✅ |
| Stack | Uma dependência nova (`pdfplumber`), usada só na borda. Migração reversível. | ✅ |

**Resultado**: sem violações. Reavaliado após o desenho: sem mudanças.

## Project Structure

### Documentation (this feature)

```text
specs/011-importacao-extrato/
├── plan.md, research.md, data-model.md, quickstart.md
├── contracts/api.md
└── tasks.md            # /speckit-tasks
```

### Source Code

```text
backend/
├── pyproject.toml                           # + pdfplumber
├── alembic/versions/0010_importacao.py
├── app/
│   ├── domain/
│   │   ├── extrato/
│   │   │   ├── __init__.py                  # LinhaExtrato, LinhaPdf, ErroExtrato, Formato
│   │   │   ├── valores.py                   # centavos, datas, decodificar
│   │   │   ├── ofx.py
│   │   │   ├── csv.py                       # nubank, inter, genérico (MapeamentoCsv)
│   │   │   ├── pdf.py                       # âncoras + linhas próximas (R4) e leitores por banco
│   │   │   └── bancos.py                    # registro código → Banco
│   │   └── importacao.py                    # normalizar, id_externo, classificar, sugerir, cobertura do lote
│   ├── models/lancamento.py                 # + id_externo, índice
│   ├── schemas/importacao.py                # BancoOut, PreviaIn/Out, ImportacaoIn/Out
│   ├── schemas/lancamento.py                # + importado
│   ├── services/pdf.py                      # pdfplumber → list[LinhaPdf]
│   ├── services/importacao.py               # prévia e confirmação
│   ├── api/routes/importacoes.py
│   └── main.py                              # registra o router
└── tests/
    ├── domain/fixtures/extratos/            # sintéticas: *.ofx, *.csv, *_pdf.txt
    ├── domain/test_extrato_*.py, test_importacao.py
    └── api/test_importacao.py

frontend/
├── app/(app)/importar/page.tsx
├── features/importacao/                     # seletor de banco, upload, mapeamento, tabela de prévia
├── lib/api/importacao.ts, lib/api/types.ts
└── components/layout/app-sidebar.tsx        # link "Importar extrato"
```

**Structure Decision**: segue as camadas do CLAUDE.md. O layout de cada banco é regra de domínio,
porque decide o que é movimentação, então fica em `domain/extrato/`. A extração de texto do PDF é
infraestrutura (`services/pdf.py`).

## Complexity Tracking

Sem violações da constituição a justificar.
