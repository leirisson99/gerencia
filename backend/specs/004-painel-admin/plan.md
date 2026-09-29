# Implementation Plan: Painel do Administrador

**Branch**: `004-painel-admin` | **Date**: 2026-09-28 | **Spec**: [spec.md](spec.md)

## Summary

Comando `python -m app.cli criar-admin` cria o único administrador com senha temporária gerada.
Rotas `GET /api/v1/admin/usuarios` (lista e busca) e `POST /api/v1/admin/usuarios/{id}/reset-senha`
(senha temporária, sessões encerradas, troca obrigatória) só para o administrador, com auditoria
em `acao_admin`. Um índice único parcial garante um administrador no banco. Decisões em
[research.md](research.md).

## Technical Context

**Language/Version**: Python 3.14 · **Dependencies**: as mesmas; nenhuma nova

**Storage**: PostgreSQL 17 — tabela `acao_admin` e índice único parcial em `usuario`
(migração `0004`, [data-model.md](data-model.md))

**Testing**: pytest — `tests/domain/test_senha_temporaria.py`, `tests/services/test_criar_admin.py`,
`tests/api/test_admin.py`

**Project Type**: web service (API HTTP); escopo só do backend

**Constraints**: admin só vê `id`, `nome`, `email`, `criado_em`; nunca escolhe senha; toda ação
auditada; logs sem senha temporária

## Constitution Check

| Princípio | Verificação | Status |
| --- | --- | --- |
| III. Domínio Puro e Teste Primeiro | Geração de senha temporária testada contra `validar_senha`; testes antes. | ✅ |
| IV. Contratos Tipados | `UsuarioAdminOut`, `SenhaTemporariaOut`; 403 `acesso_negado` no formato único. | ✅ |
| V. Contas e Isolamento | Admin criado só por comando; vê só nome/e-mail/criação; sem dado financeiro; única ação é reset com senha gerada, sessões encerradas, troca obrigatória; auditoria. | ✅ |
| VI. Escopo P0 | Só reset (sem desativar contas); um admin por índice, sem generalizar papéis. | ✅ |
| Stack | Migração `0004` reversível. | ✅ |

**Resultado**: sem violações.

## Project Structure

```text
backend/
├── alembic/versions/0004_acao_admin.py
├── app/cli.py                       # criar-admin
├── app/models/acao_admin.py
├── app/schemas/admin.py
├── app/services/admin.py            # criar_administrador, listar_usuarios, resetar_senha
├── app/services/senha.py            # + gerar_senha_temporaria
├── app/api/deps.py                  # + AdministradorDep
├── app/api/routes/admin.py
└── tests/domain/test_senha_temporaria.py, tests/services/test_criar_admin.py, tests/api/test_admin.py
```

## Complexity Tracking

Sem violações.
