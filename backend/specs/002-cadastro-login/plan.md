# Implementation Plan: Cadastro e Login de Usuários

**Branch**: `002-cadastro-login` | **Date**: 2026-09-28 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/002-cadastro-login/spec.md`

## Summary

Cadastro aberto (nome, e-mail, telefone, cargo e senha obrigatórios; data de nascimento
opcional), login com e-mail e senha, logout, troca da própria senha (inclusive obrigatória
após reset), visualização e edição do perfil. Como é a primeira feature implementada, o plano
também cria o esqueleto do backend (FastAPI, SQLAlchemy, Alembic, PostgreSQL em Docker,
pytest).

Abordagem: sessão opaca no servidor em cookie `HttpOnly` (revogável), senha com argon2id,
bloqueio de login por tentativas guardadas no banco, regras de validação e de bloqueio como
funções puras em `app/domain/` com testes escritos antes. Detalhes em [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.14 (venv existente em `backend/.venv`)

**Primary Dependencies**: FastAPI, Pydantic v2, pydantic-settings, SQLAlchemy 2.x (síncrono),
psycopg 3, Alembic, argon2-cffi, email-validator; dev: pytest, httpx, ruff. Gerenciado com `uv`.

**Storage**: PostgreSQL 17 (Docker Compose em dev; banco `gerencia_test` nos testes)

**Testing**: pytest — `tests/domain/` (funções puras) e `tests/api/` (TestClient contra
PostgreSQL real, rollback por teste)

**Target Platform**: servidor Linux (container) atrás de HTTPS; clientes web futuros no mesmo
site (necessário para o cookie `SameSite=Lax`)

**Project Type**: web service (API HTTP); escopo só do backend

**Performance Goals**: login e cadastro respondem em menos de 1 s com o hash argon2 (SC-001,
SC-002)

**Constraints**: cookie `Secure` em produção; CORS só para `FRONTEND_ORIGIN`; nenhum segredo
versionado; logs sem senha, token ou dados pessoais

**Scale/Scope**: dezenas a centenas de usuários; 7 rotas; 4 tabelas

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Verificação | Status |
| --- | --- | --- |
| I. Integridade Financeira | Feature não manipula dinheiro. | ✅ N/A |
| II. Ciclo Aberto pelo Salário | Cadastro cria a categoria de sistema "Salário" (FR-018), pré-requisito do ciclo; nenhum ciclo armazenado. | ✅ |
| III. Domínio Puro e Teste Primeiro | Regras de e-mail, telefone, senha, data de nascimento, bloqueio e expiração de sessão em `app/domain/`, puras, com `agora`/`hoje` por parâmetro, testes antes. Testes de API em PostgreSQL real. | ✅ |
| IV. API com Contratos Tipados | Schemas Pydantic de entrada e saída em todas as rotas; `extra="forbid"`; formato de erro único ([contracts/api.md](contracts/api.md)). | ✅ |
| V. Contas e Isolamento | Login e-mail + senha; e-mail único; argon2id; todas as rotas exigem sessão exceto health, cadastro e login; rotas só operam no usuário da sessão; teste de isolamento A/B; cadastro público nunca cria admin; segredos em `.env`; logs sem dados sensíveis. | ✅ |
| VI. Escopo P0 e Simplicidade | Só o pedido na spec; tabela `categoria` mínima (sem lista inicial); monólito; camadas routes → services → domain; sem cache, fila ou serviço externo. | ✅ |
| Stack | Python 3.12+, FastAPI, Pydantic v2, PostgreSQL, SQLAlchemy 2, Alembic reversível, pytest, ruff. | ✅ |

**Resultado**: sem violações. Reavaliado após a Fase 1: o desenho (4 tabelas, 7 rotas,
sessão no servidor) mantém todos os itens acima; nada a registrar em Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/002-cadastro-login/
├── plan.md              # este arquivo
├── research.md          # Fase 0
├── data-model.md        # Fase 1
├── quickstart.md        # Fase 1
├── contracts/
│   └── api.md           # Fase 1
└── tasks.md             # Fase 2 (/speckit-tasks)
```

### Source Code (repository root)

```text
backend/
├── pyproject.toml              # deps, ruff, pytest
├── docker-compose.yml          # postgres:17 (gerencia, gerencia_test)
├── docker/initdb.sql           # cria gerencia_test
├── .env.example
├── alembic.ini
├── alembic/
│   └── versions/0001_usuario_sessao_categoria.py
├── app/
│   ├── main.py                 # app, CORS, exception handlers, routers
│   ├── config.py               # Settings (pydantic-settings)
│   ├── db.py                   # engine, SessionLocal, get_db
│   ├── relogio.py              # dependência de hora (UTC e America/Sao_Paulo)
│   ├── erros.py                # ErroApi e formato único de erro
│   ├── models/
│   │   ├── usuario.py
│   │   ├── sessao.py
│   │   ├── tentativa_login.py
│   │   └── categoria.py
│   ├── schemas/
│   │   ├── erro.py
│   │   └── usuario.py          # CadastroIn, LoginIn, PerfilIn, TrocaSenhaIn, UsuarioOut
│   ├── domain/
│   │   ├── usuario.py          # normalizar_email, normalizar_telefone, validar_senha, validar_data_nascimento
│   │   └── login.py            # calcular_bloqueio, sessao_expirada
│   ├── services/
│   │   ├── senha.py            # argon2 (hash, verificar, precisa_rehash)
│   │   ├── auth.py             # cadastrar, entrar, sair, trocar_senha
│   │   └── perfil.py           # obter, atualizar
│   └── api/
│       ├── deps.py             # usuario_atual, usuario_atual_permitindo_troca
│       └── routes/
│           ├── health.py
│           ├── auth.py
│           └── me.py
└── tests/
    ├── conftest.py             # banco de teste, rollback por teste, client, relógio fixo
    ├── domain/
    │   ├── test_usuario.py
    │   └── test_login.py
    └── api/
        ├── test_cadastro.py
        ├── test_login.py
        ├── test_perfil.py
        ├── test_troca_senha.py
        └── test_isolamento.py
```

**Structure Decision**: só `backend/`, seguindo a estrutura do CLAUDE.md (`models/`,
`schemas/`, `domain/`, `services/`, `api/routes/`). O frontend está fora do escopo atual; o
contrato em [contracts/api.md](contracts/api.md) e o OpenAPI servem a qualquer cliente.

## Complexity Tracking

Sem violações da constituição a justificar.
