---

description: "Tarefas da feature 011 — Importação de Extrato"
---

# Tasks: Importação de Extrato

**Input**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/api.md](contracts/api.md), [quickstart.md](quickstart.md)

**Tests**: obrigatórios (Princípio III), escritos antes e vistos falhando. Fixtures **sintéticas**
(nunca dados de `extratos/`).

## Format: `[ID] [P?] [Story] Description`

- **[Story]**: US1 prévia e confirmação, US2 histórico e salários, US3 sem duplicar, US4 bancos e
  formatos, US5 sugestão de categoria
- Caminhos relativos a `backend/` (ou `frontend/` quando indicado)

---

## Phase 1: Setup

- [X] T001 `pdfplumber` em pyproject.toml (`uv add pdfplumber`)
- [X] T002 Migração reversível `lancamento.id_externo VARCHAR(120) NULL` + índice único parcial `uq_lancamento_usuario_id_externo` em alembic/versions/0010_importacao.py; campo no modelo app/models/lancamento.py

---

## Phase 2: Foundational — leitura de valores e OFX (testes primeiro)

- [X] T003 [P] Testes de `centavos` (`1.234,56`, `1234.56`, `-R$ 1.234,56`, `R$ -1.234,56`, `+ 999,99`, `12.34`, `0,00`, inválidos), datas (`dd/mm/aaaa`, `dd-mm-aaaa`, `aaaammdd[...]`, `dd de setembro de 2026`, `01 SET 2026`) e `decodificar` (utf-8, latin-1, BOM) em tests/domain/test_extrato_valores.py
- [X] T004 `LinhaExtrato`, `LinhaPdf`, `ErroExtrato`, `Formato` em app/domain/extrato/__init__.py; `centavos`, `data_*`, `decodificar` em app/domain/extrato/valores.py
- [X] T005 [P] Fixtures sintéticas OFX (SGML estilo Inter e Nubank, XML 2.x) e testes do `ler_ofx` (sinal por `TRNAMT`, data com fuso `[-3:BRT]`, `MEMO`/`NAME`, sem transações, arquivo não-OFX → `ErroExtrato`) em tests/domain/test_extrato_ofx.py
- [X] T006 `ler_ofx` em app/domain/extrato/ofx.py

---

## Phase 3: US1 + US3 — prévia, confirmação e sem duplicar (P1) 🎯 MVP

- [X] T007 [P] [US1] Testes puros de `normalizar_descricao`, `gerar_ids_externos` (id do banco; hash estável; ordem entre linhas idênticas), `classificar` (precedência R8, consumo de possíveis duplicadas) e `cobertura_do_lote` em tests/domain/test_importacao.py
- [X] T008 [US1] Implementar app/domain/importacao.py
- [X] T009 [US1] Schemas `BancoOut`, `MapeamentoCsvIn`, `PreviaIn`, `LinhaPreviaOut`, `PreviaOut`, `LinhaImportacaoIn`, `ImportacaoIn`, `ImportacaoOut` em app/schemas/importacao.py; `importado` em `LancamentoOut` (app/schemas/lancamento.py, propriedade no modelo)
- [X] T010 [US1] Testes de API: prévia OFX não grava; confirmação cria realizados com categoria escolhida; tipo ≠ categoria → 422 `linhas.i.categoria_id` e nada gravado; base64 inválido/arquivo ruim → 422 `extrato_invalido`; > 2 MB → 413; reimportar → `ja_importada` e `criados: 0, ignoradas: n`; manual igual → `possivel_duplicada`; dois cafés iguais; categoria de outro usuário → 404; isolamento de `ja_importada` entre usuários; `importado` no `LancamentoOut`; 401 sem sessão, em tests/api/test_importacao.py
- [X] T011 [US1] Serviço `previa` e `confirmar` (trava, validação por linha, descarte de ids existentes, cobertura do lote, gravação, previstos do novo ciclo aberto, `IntegrityError` → 409 `conflito_importacao`) em app/services/importacao.py
- [X] T012 [US1] Rotas `GET /importacoes/bancos`, `POST /importacoes/previa`, `POST /importacoes` em app/api/routes/importacoes.py; registrar em app/main.py

---

## Phase 4: US2 — histórico e salários (P1)

- [X] T013 [US2] Testes de API: usuário sem salário importa lote com salários → ciclos criados; linha antes do primeiro salário existente → `antes_do_primeiro_ciclo` e confirmar → 409; salário futuro no lote → 422; salários passados não geram previstos; salário mais recente gera previstos do novo ciclo aberto, em tests/api/test_importacao.py
- [X] T014 [US2] Ajustes no serviço até T013 passar

---

## Phase 5: US4 — bancos e formatos (P1)

- [X] T015 [P] [US4] Fixtures sintéticas e testes de CSV: Nubank (`Data,Valor,Identificador,Descrição`), Inter (preâmbulo, `;`, `-1.234,56`, Histórico + Descrição), genérico (valor único; crédito/débito; formatos de data; separadores; pular linhas; coluna inexistente → erro) em tests/domain/test_extrato_csv.py
- [X] T016 [US4] app/domain/extrato/csv.py
- [X] T017 [P] [US4] Fixtures sintéticas de PDF (listas de `LinhaPdf` em texto) e testes dos leitores Itaú (ignora `SALDO DO DIA`, várias páginas), Mercado Pago (descrição acima/abaixo, ID da operação), Neon (`\x00R$` negativo, hora ignorada), Nubank (blocos de entradas/saídas por dia, continuação abaixo), Inter (cabeçalho de dia, `-R$`); layout desconhecido → `ErroExtrato` em tests/domain/test_extrato_pdf.py
- [X] T018 [US4] app/domain/extrato/pdf.py
- [X] T019 [US4] Registro de bancos em app/domain/extrato/bancos.py; `services/pdf.py` (pdfplumber → `LinhaPdf`, sem texto → `pdf_sem_texto`); testes de API de `GET /importacoes/bancos`, `formato_indisponivel`, CSV genérico sem mapeamento → 422 e PDF sem texto (PDF mínimo gerado no teste)
- [X] T020 [US4] Validação manual com os extratos reais (quickstart, passos 2 e 3), por script local fora do repositório; ajustar leitores se a contagem ou os totais não baterem

---

## Phase 6: US5 — sugestão de categoria (P2)

- [X] T021 [US5] Testes puros de `sugerir_categoria` (maiúsculas/acentos/espaços, mais recente vence, tipo diferente → nada, desconhecida → nada) em tests/domain/test_importacao.py; testes de API (categoria desativada não é sugerida) em tests/api/test_importacao.py
- [X] T022 [US5] Histórico de descrições no serviço (uma consulta) e sugestão na prévia

---

## Phase 7: Frontend

- [X] T023 [P] Tipos e cliente da API em frontend/lib/api/types.ts e frontend/lib/api/importacao.ts
- [X] T024 Tela frontend/app/(app)/importar/page.tsx e componentes em frontend/features/importacao/ (banco e formato, upload → base64, mapeamento do CSV genérico, tabela de prévia com checkbox, categoria e selo de situação, confirmar com resultado e erros por linha); link no menu em frontend/components/layout/app-sidebar.tsx
- [X] T025 `npx tsc --noEmit` e `npm run lint` limpos

---

## Phase 8: Polish

- [X] T026 `uv run alembic downgrade -1 && uv run alembic upgrade head` e `alembic check` sem diferenças
- [X] T027 `uv run ruff check . && uv run ruff format --check .` e `uv run pytest` verdes

---

## Dependencies & Execution Order

- Phase 1 → Phase 2 → US1 (MVP com OFX). US2 e US4 dependem de US1; US5 depende de US1.
- Os leitores de CSV e PDF (T015–T018) podem ser feitos em paralelo com US2.
- O frontend (Phase 7) depende do contrato estável (US1 + US4).
