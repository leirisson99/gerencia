---

description: "Tarefas da feature 002 — Cadastro e Login de Usuários"
---

# Tasks: Cadastro e Login de Usuários

**Input**: Design documents from `specs/002-cadastro-login/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/api.md](contracts/api.md), [quickstart.md](quickstart.md)

**Tests**: obrigatórios. A constituição (Princípio III) exige teste escrito antes para toda regra de
domínio e testes de API em PostgreSQL real. Em cada fase, as tarefas de teste vêm primeiro e
MUST falhar antes da implementação.

**Organization**: tarefas agrupadas por história de usuário da spec.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode rodar em paralelo (arquivos diferentes, sem dependência pendente)
- **[Story]**: história da spec (US1 = Criar conta, US2 = Entrar e sair, US3 = Trocar senha,
  US4 = Ver e editar dados)
- Caminhos relativos a `backend/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: criar o projeto backend do zero

- [X] T001 Criar `pyproject.toml` com `requires-python = ">=3.12"`, dependências `fastapi`, `uvicorn[standard]`, `pydantic>=2`, `pydantic-settings`, `sqlalchemy>=2`, `psycopg[binary]>=3`, `alembic`, `argon2-cffi`, `email-validator`; grupo dev `pytest`, `httpx`, `ruff`; seção `[tool.ruff]` (line-length 100, target py312, regras `E,F,I,UP,B,SIM`) e `[tool.pytest.ini_options]` (`testpaths = ["tests"]`) em pyproject.toml
- [X] T002 [P] Criar `docker-compose.yml` com serviço `db` (`postgres:17`, porta 5432, usuário/senha/banco `gerencia` vindos de variáveis, volume nomeado) montando `docker/initdb.sql` em `/docker-entrypoint-initdb.d/` em docker-compose.yml
- [X] T003 [P] Criar script que cria o banco `gerencia_test` em docker/initdb.sql
- [X] T004 [P] Criar `.env.example` com `DATABASE_URL`, `TEST_DATABASE_URL`, `FRONTEND_ORIGIN=http://localhost:3000`, `COOKIE_SECURE=false`, `SESSAO_DIAS_INATIVIDADE=30` em .env.example
- [X] T005 [P] Criar `.gitignore` do backend ignorando `.venv/`, `.env`, `__pycache__/`, `.pytest_cache/`, `.ruff_cache/` em .gitignore
- [X] T006 Rodar `uv sync` e inicializar o Alembic (`alembic init alembic`), configurando `alembic/env.py` para ler a URL de `app.config.Settings` e usar `app.models.Base.metadata` em alembic/env.py
- [X] T007 [P] Criar pacotes vazios `app/__init__.py`, `app/models/__init__.py`, `app/schemas/__init__.py`, `app/domain/__init__.py`, `app/services/__init__.py`, `app/api/__init__.py`, `app/api/routes/__init__.py`, `tests/__init__.py`, `tests/domain/__init__.py`, `tests/api/__init__.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: configuração, banco, erros, sessão e autenticação usados por todas as histórias

**⚠️ CRITICAL**: nenhuma história começa antes desta fase terminar

### Testes primeiro

- [X] T008 [P] Escrever testes de `sessao_expirada(ultimo_uso_em, agora, dias=30)`: 29 dias e 23h59 → válida; exatamente 30 dias → expirada; 31 dias → expirada em tests/domain/test_login.py
- [X] T009 Criar fixtures: engine no `TEST_DATABASE_URL`, `alembic upgrade head` uma vez por sessão, conexão com transação externa e `Session(join_transaction_mode="create_savepoint")` desfeita a cada teste, override de `get_db`, override de `relogio` com hora fixa ajustável, `client` (`TestClient`) e helper `cadastrar_e_logar(client, **dados)` em tests/conftest.py

### Infraestrutura

- [X] T010 [P] Implementar `Settings` (pydantic-settings, lê `.env`): `database_url`, `test_database_url`, `frontend_origin`, `cookie_secure: bool`, `sessao_dias_inatividade: int = 30` em app/config.py
- [X] T011 [P] Implementar engine, `SessionLocal` e dependência `get_db` (SQLAlchemy 2 síncrono, psycopg 3) em app/db.py
- [X] T012 [P] Implementar dependência `Relogio` com `agora_utc() -> datetime` e `hoje_sp() -> date` (fuso `America/Sao_Paulo`) em app/relogio.py
- [X] T013 [P] Implementar `ErroApi(status, codigo, mensagem, campos=None)` e os handlers que convertem `ErroApi`, `RequestValidationError` (→ 422 `validacao` com `campos` por nome de campo) e erros não tratados (→ 500 sem detalhes) para `{"erro": {"codigo", "mensagem", "campos"}}` em app/erros.py
- [X] T014 [P] Criar schema `ErroOut` com o formato de erro de contracts/api.md em app/schemas/erro.py
- [X] T015 Criar `Base` declarativa e reexportar os modelos em app/models/__init__.py
- [X] T016 [P] Criar modelo `Usuario`: `id` bigint identity; `nome` varchar(120) "obrigatório, sem espaços nas pontas, não vazio"; `email` varchar(254) "normalizado (minúsculo, sem espaços), UNIQUE"; `senha_hash` varchar(255); `telefone` varchar(11) "só dígitos, 10 ou 11"; `cargo` varchar(80) obrigatório; `data_nascimento` date null; `papel` varchar(10) com CHECK `usuario | admin`, default `usuario`; `troca_senha_obrigatoria` boolean default false; `criado_em` e `atualizado_em` timestamptz default now() em app/models/usuario.py
- [X] T017 [P] Criar modelo `Sessao`: `id` bigint identity; `usuario_id` FK → usuario.id ON DELETE CASCADE, indexado; `token_hash` char(64) UNIQUE (SHA-256 hex); `criada_em` e `ultimo_uso_em` timestamptz em app/models/sessao.py
- [X] T018 [P] Criar modelo `Categoria`: `id` bigint identity; `usuario_id` FK → usuario.id ON DELETE CASCADE, indexado; `nome` varchar(60); `tipo` varchar(7) com CHECK `entrada | saida`; `ativa` boolean default true; `sistema` boolean default false; índice único parcial em `usuario_id` onde `sistema = true AND nome = 'Salário'` em app/models/categoria.py
- [X] T019 Gerar e revisar a migração com `usuario`, `sessao` e `categoria`, com `downgrade` que remove tudo, em alembic/versions/0001_usuario_sessao_categoria.py
- [X] T020 Implementar `sessao_expirada` para passar T008 em app/domain/login.py
- [X] T021 [P] Implementar `hash_senha`, `verificar_senha` (retorna False em vez de exceção) e `precisa_rehash` com `argon2.PasswordHasher` padrão, e `HASH_FICTICIO` gerado no import para igualar tempo com e-mail inexistente em app/services/senha.py
- [X] T022 Implementar serviço de sessão: `criar_sessao(db, usuario, agora) -> token` (`secrets.token_urlsafe(32)`, guarda só `sha256`), `resolver_sessao(db, token, agora)` (apaga e devolve None se `sessao_expirada`; senão atualiza `ultimo_uso_em`), `encerrar_sessao`, `encerrar_outras_sessoes(db, usuario_id, sessao_atual_id)` em app/services/sessao.py
- [X] T023 Implementar helpers de cookie `definir_cookie_sessao(response, token)` (`HttpOnly`, `SameSite=Lax`, `Secure=settings.cookie_secure`, `Path=/`, `max_age` = 30 dias) e `apagar_cookie_sessao(response)` em app/api/cookies.py
- [X] T024 Implementar dependências `usuario_atual_permitindo_troca` (lê cookie `sessao`; sem cookie ou sessão inválida → `ErroApi(401, "nao_autenticado")`) e `usuario_atual` (idem + `troca_senha_obrigatoria` → `ErroApi(403, "troca_senha_obrigatoria")`) em app/api/deps.py
- [X] T025 [P] Criar schema `UsuarioOut` (`id`, `nome`, `email`, `telefone`, `cargo`, `data_nascimento`, `troca_senha_obrigatoria`, `criado_em`; nunca `senha_hash` nem `papel`) em app/schemas/usuario.py
- [X] T026 [P] Implementar `GET /health` → `{"status": "ok"}` em app/api/routes/health.py
- [X] T027 Implementar `GET /api/v1/me` → `UsuarioOut` usando `usuario_atual` em app/api/routes/me.py
- [X] T028 Montar a app: routers `health`, `auth` (prefixo `/api/v1/auth`), `me` (prefixo `/api/v1`), handlers de erro, CORS só para `settings.frontend_origin` com `allow_credentials=True`, e middleware que recusa com 415 requisições `POST/PUT/PATCH/DELETE` sem `Content-Type: application/json` quando têm corpo em app/main.py

**Checkpoint**: `uv run pytest tests/domain` verde; `GET /health` responde; `GET /api/v1/me` sem cookie → 401 `nao_autenticado`

---

## Phase 3: User Story 1 - Criar conta (Priority: P1) 🎯 MVP

**Goal**: qualquer pessoa cria uma conta e já entra logada; a categoria "Salário" é criada

**Independent Test**: `POST /api/v1/auth/cadastro` com dados válidos → 201 + cookie, e `GET /api/v1/me` devolve os dados; dados inválidos ou e-mail repetido → recusa com o campo indicado

### Tests for User Story 1 ⚠️

- [X] T029 [P] [US1] Escrever testes de `normalizar_email` (`"  ANA@Exemplo.com "` → `"ana@exemplo.com"`), `normalizar_telefone` (`"(11) 98765-4321"` → `"11987654321"`; `"1133334444"` válido; `"123"`, `"0198765432"` (DDD 01), `"11887654321"` (11 dígitos sem 9) inválidos), `validar_senha` (`"abc12345"` ok; `"abcdefgh"`, `"12345678"`, 7 caracteres, 129 caracteres inválidos), `validar_data_nascimento` (1900-01-01 e hoje ok; 1899-12-31 e amanhã inválidos) e `limpar_texto` (`"   "` → inválido) em tests/domain/test_usuario.py
- [X] T030 [P] [US1] Escrever testes de API do cadastro: cenários 1–6 da US1 da spec (201 + cookie + `UsuarioOut`; com data de nascimento; cada obrigatório faltando → 422 com `campos`; `ANA@Exemplo.com` repetido → 409 `email_ja_cadastrado`; telefone/senha/data inválidos → 422; corpo com `"papel": "admin"` → 422 e nenhuma conta admin); resposta nunca contém `senha`/`senha_hash`; após cadastro existe categoria `("Salário", "entrada", sistema=True)` para o usuário em tests/api/test_cadastro.py

### Implementation for User Story 1

- [X] T031 [US1] Implementar `normalizar_email`, `normalizar_telefone`, `validar_senha`, `validar_data_nascimento(data, hoje)` e `limpar_texto(valor, max_len)` levantando `ValueError` com mensagem em português, para passar T029, em app/domain/usuario.py
- [X] T032 [US1] Criar schema `CadastroIn` (`model_config = ConfigDict(extra="forbid")`; `nome` ≤120, `email: EmailStr` ≤254, `telefone`, `cargo` ≤80, `senha` 8–128, `data_nascimento: date | None = None`) com validadores que chamam as funções de app/domain/usuario.py (a data usa `hoje_sp()`) em app/schemas/usuario.py
- [X] T033 [US1] Implementar `cadastrar(db, dados, agora) -> tuple[Usuario, token]`: cria `Usuario` com `papel="usuario"` e `hash_senha`, cria a categoria "Salário" de sistema, cria a sessão, tudo numa transação; `IntegrityError` no e-mail → `ErroApi(409, "email_ja_cadastrado")` em app/services/auth.py
- [X] T034 [US1] Implementar `POST /api/v1/auth/cadastro` → 201 `UsuarioOut` + `definir_cookie_sessao` em app/api/routes/auth.py

**Checkpoint**: T029 e T030 verdes; US1 funciona sozinha

---

## Phase 4: User Story 2 - Entrar e sair (Priority: P1)

**Goal**: login com e-mail e senha, mensagem genérica, bloqueio após 5 falhas, logout

**Independent Test**: cadastrar, sair, entrar com a senha certa → 200; senha errada → 401 genérico; 5 falhas → 429; após logout, rota protegida → 401

### Tests for User Story 2 ⚠️

- [X] T035 [P] [US2] Escrever testes de `calcular_bloqueio(falhas: list[datetime], agora) -> datetime | None`: 4 falhas em 15 min → None; 5 falhas em 15 min → bloqueado até 5ª + 15 min; 5 falhas espalhadas em 20 min → None; bloqueio vencido → None e falhas anteriores ao fim do bloqueio não contam; lista vazia → None em tests/domain/test_login.py
- [X] T036 [P] [US2] Escrever testes de API do login: cenários 1–5 da US2 da spec (200 + cookie + `UsuarioOut`; senha errada e e-mail inexistente → mesmo 401 `credenciais_invalidas` com o mesmo corpo; e-mail com maiúsculas/espaços entra; 5 falhas → 6ª com senha certa dá 429 `login_bloqueado` com `Retry-After`, e o mesmo para e-mail inexistente; após avançar o relógio 15 min, entra; login bem-sucedido zera as falhas; logout → 204, cookie apagado e `GET /api/v1/me` → 401; sessão com `ultimo_uso_em` há 30 dias → 401) em tests/api/test_login.py

### Implementation for User Story 2

- [X] T037 [P] [US2] Criar modelo `TentativaLogin`: `id` bigint identity; `email_normalizado` varchar(254) "sem FK (e-mail pode não existir)"; `ocorrida_em` timestamptz; índice em (`email_normalizado`, `ocorrida_em`) em app/models/tentativa_login.py
- [X] T038 [US2] Gerar a migração de `tentativa_login` com `downgrade` em alembic/versions/0002_tentativa_login.py
- [X] T039 [US2] Implementar `calcular_bloqueio` (janela de 15 min, 5 falhas, bloqueio de 15 min a partir da 5ª) para passar T035 em app/domain/login.py
- [X] T040 [US2] Criar schema `LoginIn` (`email: str`, `senha: str`, `extra="forbid"`) em app/schemas/usuario.py
- [X] T041 [US2] Implementar `entrar(db, email, senha, agora) -> tuple[Usuario, token]`: normaliza e-mail; apaga falhas com mais de 24 h; se `calcular_bloqueio` → `ErroApi(429, "login_bloqueado")` com segundos restantes, sem verificar senha; se usuário inexistente verifica contra `HASH_FICTICIO`; falha → grava `TentativaLogin` e `ErroApi(401, "credenciais_invalidas", "E-mail ou senha inválidos.")`; sucesso → apaga falhas do e-mail, refaz hash se `precisa_rehash`, cria sessão; e `sair(db, sessao)` em app/services/auth.py
- [X] T042 [US2] Implementar `POST /api/v1/auth/login` (200 + cookie; 429 com header `Retry-After`) e `POST /api/v1/auth/logout` (204, usa `usuario_atual_permitindo_troca`, encerra a sessão e apaga o cookie) em app/api/routes/auth.py

**Checkpoint**: T035 e T036 verdes; US1 e US2 funcionam juntas e separadas

---

## Phase 5: User Story 3 - Trocar a própria senha (Priority: P1)

**Goal**: troca de senha com a senha atual, encerrando as outras sessões; troca obrigatória liberada só para essa rota e logout

**Independent Test**: logar em dois clientes, trocar a senha no primeiro → 204; o segundo recebe 401; login com a nova senha funciona

### Tests for User Story 3 ⚠️

- [X] T043 [P] [US3] Escrever testes de API da troca de senha: cenários 1–4 da US3 da spec (204 e outra sessão → 401, sessão atual segue válida; senha atual errada → 400 `senha_atual_incorreta`; nova senha fraca ou igual à atual → 422; usuário com `troca_senha_obrigatoria = True` (marcado direto no banco): login devolve o flag, `GET /api/v1/me` → 403 `troca_senha_obrigatoria`, logout liberado, `PUT /api/v1/me/senha` → 204 e depois `GET /api/v1/me` → 200 com o flag falso) em tests/api/test_troca_senha.py

### Implementation for User Story 3

- [X] T044 [US3] Criar schema `TrocaSenhaIn` (`senha_atual: str`, `nova_senha` validada por `validar_senha`, `extra="forbid"`) em app/schemas/usuario.py
- [X] T045 [US3] Implementar `trocar_senha(db, usuario, sessao_atual, senha_atual, nova_senha, agora)`: senha atual errada → `ErroApi(400, "senha_atual_incorreta")`; nova igual à atual → `ErroApi(422, "validacao", campos={"nova_senha": ...})`; grava novo hash, zera `troca_senha_obrigatoria`, atualiza `atualizado_em` e chama `encerrar_outras_sessoes` em app/services/auth.py
- [X] T046 [US3] Implementar `PUT /api/v1/me/senha` → 204 usando `usuario_atual_permitindo_troca` em app/api/routes/me.py

**Checkpoint**: T043 verde; as três histórias P1 funcionam

---

## Phase 6: User Story 4 - Ver e editar os próprios dados (Priority: P2)

**Goal**: ver o próprio perfil e editar nome, telefone, cargo e data de nascimento; e-mail não muda; nenhum dado de outro usuário é acessível

**Independent Test**: `PATCH /api/v1/me` com telefone novo → 200 com valor normalizado; com `email` → 422; a sessão de A nunca lê nem altera dados de B

### Tests for User Story 4 ⚠️

- [X] T047 [P] [US4] Escrever testes de API do perfil: cenários 1–6 da US4 da spec (`GET /api/v1/me` sem senha; `PATCH` de nome/telefone/cargo/data → 200 e valores normalizados; nome/telefone/cargo vazios ou inválidos → 422; `data_nascimento: null` remove a data; corpo com `email` ou campo desconhecido → 422; `PATCH` sem nenhum campo → 200 sem mudança) em tests/api/test_perfil.py
- [X] T048 [P] [US4] Escrever testes de isolamento: com usuários A e B, a sessão de A em `GET/PATCH /api/v1/me` e `PUT /api/v1/me/senha` só lê e altera A, e os dados de B continuam iguais em tests/api/test_isolamento.py

### Implementation for User Story 4

- [X] T049 [US4] Criar schema `PerfilIn` (`nome`, `telefone`, `cargo`, `data_nascimento`, todos opcionais, mesmas validações de `CadastroIn`, `extra="forbid"`; distinguir campo ausente de `null` via `model_fields_set`) em app/schemas/usuario.py
- [X] T050 [US4] Implementar `atualizar_perfil(db, usuario, dados, agora)` aplicando só os campos enviados, com `data_nascimento = None` quando enviado `null`, e atualizando `atualizado_em` em app/services/perfil.py
- [X] T051 [US4] Implementar `PATCH /api/v1/me` → 200 `UsuarioOut` usando `usuario_atual` em app/api/routes/me.py

**Checkpoint**: todas as histórias funcionam de forma independente

---

## Phase 7: Polish & Cross-Cutting Concerns

- [X] T052 [P] Configurar logging da app (nível por variável de ambiente) sem registrar corpo de requisição, cookies, senhas, tokens, e-mail, telefone ou data de nascimento em app/main.py
- [X] T053 [P] Adicionar teste que busca em todas as respostas dos testes de API por `senha`, `senha_hash` e `papel` e falha se aparecerem em tests/api/test_cadastro.py
- [X] T054 Verificar reversibilidade: `uv run alembic downgrade base && uv run alembic upgrade head` sem erros
- [X] T055 Atualizar a seção "Comandos" com `docker compose up -d db` e remover a frase "Ajuste esta seção quando o projeto for criado" em CLAUDE.md
- [X] T056 Rodar `uv run ruff check . && uv run ruff format .` e `uv run pytest`, tudo verde
- [X] T057 Executar a validação manual de quickstart.md (passos 1–8)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sem dependências
- **Foundational (Phase 2)**: depende do Setup; bloqueia todas as histórias
- **US1–US4 (Phases 3–6)**: dependem só da Foundational
- **Polish (Phase 7)**: depois das histórias desejadas

### User Story Dependencies

- **US1 (P1)**: só Foundational
- **US2 (P1)**: só Foundational. Os testes usam o helper `cadastrar_e_logar` de T009, que chama o cadastro (US1); se US2 for feita antes de US1, o helper cria o usuário direto no banco
- **US3 (P1)**: só Foundational (mesma observação sobre o helper)
- **US4 (P2)**: só Foundational (mesma observação sobre o helper)

### Within Each User Story

- Testes escritos e falhando antes da implementação
- Domínio → schemas → serviços → rotas
- Arquivos compartilhados (`app/schemas/usuario.py`, `app/services/auth.py`, `app/api/routes/auth.py`, `app/api/routes/me.py`) são editados em sequência, nunca em paralelo

### Parallel Opportunities

- Setup: T002, T003, T004, T005, T007
- Foundational: T008; T010–T014; T016–T018; T021; T025–T026
- Em cada história, as tarefas de teste marcadas [P]
- US2 T037 em paralelo aos testes T035/T036

---

## Parallel Example: User Story 1

```bash
# Testes da US1 juntos (devem falhar):
Task: "Testes de domínio de usuário em tests/domain/test_usuario.py"
Task: "Testes de API do cadastro em tests/api/test_cadastro.py"
```

## Parallel Example: User Story 2

```bash
Task: "Testes de calcular_bloqueio em tests/domain/test_login.py"
Task: "Testes de API do login em tests/api/test_login.py"
Task: "Modelo TentativaLogin em app/models/tentativa_login.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1: Setup
2. Phase 2: Foundational
3. Phase 3: US1 (cadastro já deixa a pessoa logada)
4. **Parar e validar**: T029/T030 verdes e passos 1–2 do quickstart

### Incremental Delivery

1. Setup + Foundational → base pronta
2. US1 → cadastro
3. US2 → login, bloqueio, logout
4. US3 → troca de senha (pré-requisito da feature 003)
5. US4 → perfil e isolamento
6. Polish → logging, migração reversível, lint, quickstart

---

## Notes

- [P] = arquivos diferentes, sem dependência pendente
- Commits pequenos em Conventional Commits (`test:` antes de `feat:` em cada regra de domínio)
- Nunca usar `float` nem SQLite; nenhum segredo no repositório
- Parar em cada checkpoint para validar a história isoladamente
