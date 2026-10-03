# Implementation Plan: Atividade do Usuário no Painel do Administrador

**Branch**: `018-atividade-usuario` | **Date**: 2026-10-02 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/018-atividade-usuario/spec.md`

## Summary

Nova tabela `evento_uso` (só usuário, tipo e data e hora), gravada pelas funções públicas dos
`services/` na mesma transação da ação, de modo que ação que falha não deixa evento. Duas rotas
novas no admin:

- `GET /admin/usuarios/{id}`: conta, último acesso, sessões abertas, contagens por
  funcionalidade e ações do administrador;
- `GET /admin/usuarios/{id}/eventos?antes=`: linha do tempo paginada por id.

Ver a atividade grava `ver_atividade` em `acao_admin`, no máximo uma vez a cada 30 minutos por
par administrador e conta. Um comando `limpar-eventos` no cron aplica a retenção de 12 meses.
No frontend: página de detalhe a partir da lista de contas e aviso de transparência no
cadastro e no perfil.

## Technical Context

**Language/Version**: Python 3.12 (backend) e TypeScript, Next.js (frontend em `../frontend`)

**Primary Dependencies**: FastAPI, SQLAlchemy 2, Alembic, Pydantic v2; Next.js + shadcn/ui

**Storage**: PostgreSQL 17 (uma tabela nova e um `CHECK` alterado)

**Testing**: pytest com PostgreSQL (`gerencia_test`); domínio em `tests/domain/`, rotas em
`tests/api/`

**Target Platform**: servidor Linux (Easypanel): API, cron (supercronic) e frontend

**Project Type**: aplicação web (API + frontend)

**Performance Goals**: detalhe e página de eventos com o mesmo custo para 10 mil ou 10 eventos
(índice `(usuario_id, id DESC)`, keyset, contagens numa consulta só)

**Constraints**: zero valor ou conteúdo nas respostas e na tabela; um evento por ação
bem-sucedida; abertura auditada

**Scale/Scope**: poucas centenas de contas; 27 tipos de evento; 2 rotas; 1 comando; 1 página
nova e 2 avisos no frontend

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.* Constituição 6.0.0.

| Princípio | Verificação | Status |
| --- | --- | --- |
| I. Integridade financeira | Nenhum valor é lido para exibição nem alterado; o evento entra na transação existente sem mudar regras de saldo. | ✅ |
| II. Ciclo derivado | Não muda. Os previstos gerados ao abrir o ciclo não viram eventos. | ✅ |
| III. Domínio puro e teste primeiro | `domain/atividade.py` (`precisa_registrar_visita`, `limite_retencao`, `tipo_edicao_lembrete`, `fatiar_pagina`) testado antes; um teste de API por tipo de evento e pelos cenários de falha. | ✅ |
| IV. Contratos tipados | `DetalheContaOut` e `PaginaEventosOut` em Pydantic, `tipo` como `Literal`, erros no formato único. | ✅ |
| V. Isolamento | Exatamente o que a 6.0.0 permite: uso sem conteúdo, evento só com usuário, tipo e data e hora, abertura registrada, aviso ao usuário. Usuário comum recebe 403; conta do admin ou inexistente, 404. Um teste varre as respostas atrás de valores e textos plantados. Logs do `limpar-eventos` só com contagem. | ✅ |
| VI. Escopo e simplicidade | Pedido explícito (opção B). Sem papéis novos, filas ou serviços: o cron já existe. Sem filtros na linha do tempo. | ✅ |

**Re-check pós-design**: sem violações. Complexity Tracking vazio.

## Project Structure

### Documentation (this feature)

```text
specs/018-atividade-usuario/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/admin-atividade.md
├── checklists/requirements.md
└── tasks.md             # /speckit-tasks
```

### Source Code

```text
backend/
├── alembic/versions/0017_evento_uso.py          # novo
├── app/
│   ├── models/evento_uso.py                     # novo: EventoUso + TIPOS_EVENTO
│   ├── models/acao_admin.py                     # + ACAO_VER_ATIVIDADE no CHECK
│   ├── domain/atividade.py                      # novo: regras puras
│   ├── schemas/admin.py                         # + DetalheContaOut, PaginaEventosOut
│   ├── services/evento_uso.py                   # novo: registrar(), limpar_antigos()
│   ├── services/admin.py                        # + obter_detalhe(), listar_eventos()
│   ├── services/{auth,perfil,lancamento,importacao,categoria,recorrencia,
│   │            divida,cartela,servico,lembrete,push}.py   # + registrar(...)
│   ├── api/routes/admin.py                      # + 2 rotas
│   └── cli.py                                   # + limpar-eventos
├── crontab                                      # + linha limpar-eventos (06:00 UTC)
└── tests/
    ├── domain/test_atividade.py                 # novo
    └── api/test_admin_atividade.py              # novo (detalhe, eventos, auditoria, privacidade)

frontend/
├── app/(admin)/admin/contas/[id]/page.tsx       # novo
├── features/admin/detalhe-conta.tsx             # novo: cartões de acesso e contagens
├── features/admin/linha-tempo.tsx               # novo: lista + "carregar mais"
├── features/admin/lista-contas.tsx              # linha clicável → detalhe
├── lib/api/admin.ts                             # + obterDetalhe, listarEventos, rótulos
├── features/auth/form-cadastro.tsx              # + aviso
└── features/perfil/form-perfil.tsx              # + aviso
```

**Structure Decision**: o padrão de camadas que já existe. Regra pura em `domain/atividade.py`;
`services/` grava e consulta; as rotas só validam e chamam. A página de detalhe usa largura
total, como as demais páginas de dados.

## Ordem de implementação

1. Domínio e testes (`domain/atividade.py`).
2. Modelo, migração e `services/evento_uso.py`.
3. Gravação nos services, com teste por tipo e pelos casos de falha (US2).
4. Detalhe e contagens (US1), eventos paginados (US2), ações do admin (US3), auditoria
   `ver_atividade`.
5. Comando `limpar-eventos` e linha no `crontab`.
6. Frontend: detalhe, linha do tempo e avisos (US4).
7. CLAUDE.md: glossário (Evento de uso) e modelo de dados (`evento_uso`), pendência da emenda
   6.0.0.

## Complexity Tracking

Nenhuma violação a justificar.
