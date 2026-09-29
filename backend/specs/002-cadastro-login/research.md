# Research: Cadastro e Login de Usuários

Decisões técnicas da feature 002. Não há itens NEEDS CLARIFICATION pendentes.

## R1. Mecanismo de sessão

- **Decision**: sessão opaca guardada no servidor (tabela `sessao`). O token é gerado com
  `secrets.token_urlsafe(32)`, só o SHA-256 dele é guardado, e ele trafega num cookie
  `HttpOnly`, `Secure` (fora de dev), `SameSite=Lax`, `Path=/`.
- **Rationale**: a spec exige encerrar as outras sessões na troca de senha (FR-014), expirar
  por inatividade (FR-011) e, na feature 004, derrubar as sessões no reset. Com sessão no
  servidor isso é um `DELETE`/`UPDATE`. Cookie `HttpOnly` protege o token contra XSS no
  frontend. SHA-256 basta porque o token tem 256 bits de entropia (não precisa de hash lento).
- **Alternatives considered**:
  - JWT sem estado: revogação exige lista negra ou versão de token no usuário, ou seja,
    volta a consultar o banco, com mais complexidade.
  - Token em `Authorization: Bearer` guardado no `localStorage`: exposto a XSS.

## R2. Proteção contra CSRF

- **Decision**: `SameSite=Lax` no cookie + toda requisição que altera estado exige
  `Content-Type: application/json` (o que força preflight de CORS em origem estranha) + CORS
  restrito à origem do frontend (`FRONTEND_ORIGIN`), com `allow_credentials=True`.
- **Rationale**: cobre o CSRF clássico sem token CSRF extra. Frontend e API devem ficar no
  mesmo site (ex.: `app.dominio` e `api.dominio`) para o cookie `Lax` funcionar.
- **Alternatives considered**: token CSRF de dupla submissão — mais peças sem ganho real
  dadas as outras camadas.

## R3. Hash de senha

- **Decision**: argon2id com `argon2-cffi` (`PasswordHasher` com parâmetros padrão da lib) e
  `check_needs_rehash` no login.
- **Rationale**: exigido pela constituição (argon2 ou bcrypt); argon2id é o recomendado atual
  e não tem o limite de 72 bytes do bcrypt (a spec aceita até 128 caracteres).
- **Alternatives considered**: bcrypt (limite de 72 bytes), `passlib` (sem manutenção ativa).

## R4. Bloqueio de login por tentativas (FR-009)

- **Decision**: tabela `tentativa_login` com uma linha por falha (`email_normalizado`,
  `ocorrida_em`). Regra pura em `domain/login.py`:
  - considera só falhas posteriores ao último login bem-sucedido e ao fim do último bloqueio;
  - se houver 5 falhas dentro de uma janela de 15 minutos, `bloqueado_ate = hora da 5ª + 15
    min`;
  - tentativas durante o bloqueio são recusadas sem verificar a senha e não contam.
  Login bem-sucedido apaga as falhas daquele e-mail. Falhas com mais de 24 h são apagadas no
  próprio fluxo de login (sem job agendado).
- **Rationale**: funciona para e-mails inexistentes (não depende de `usuario`), não revela se
  o e-mail existe e é testável como função pura recebendo `agora`.
- **Alternatives considered**: contador na tabela `usuario` (não cobre e-mail inexistente e
  vaza existência); limitador em memória (perde estado ao reiniciar, não funciona com mais de
  um processo).

## R5. Não revelar existência de e-mail no login

- **Decision**: quando o e-mail não existe, o login verifica a senha contra um hash argon2
  fixo gerado na inicialização, para igualar o tempo de resposta, e devolve o mesmo 401
  genérico. A resposta de bloqueio (429) é igual para e-mails existentes e inexistentes.
- **Rationale**: SC-004. O cadastro continua informando "e-mail já cadastrado" (aceito na
  spec, Assumptions).

## R6. Validação e normalização

- **Decision**: funções puras em `domain/usuario.py`:
  - `normalizar_email`: `strip()` + `lower()`; formato validado com `email-validator` no
    schema (`EmailStr`).
  - `normalizar_telefone`: mantém só dígitos; aceita 10 ou 11 dígitos; DDD entre 11 e 99; com
    11 dígitos, o número começa com 9.
  - `validar_senha`: 8 a 128 caracteres, ao menos uma letra e um dígito.
  - `validar_data_nascimento(data, hoje)`: entre 01/01/1900 e hoje.
  - Texto (nome, cargo): `strip()`; vazio é inválido. Limites: nome 120, cargo 80, e-mail 254.
- **Rationale**: regras de domínio nascem com teste (Princípio III); schemas Pydantic só
  chamam essas funções.

## R7. Troca de senha obrigatória (FR-015)

- **Decision**: a dependência `usuario_atual` recusa com 403 `troca_senha_obrigatoria`
  qualquer rota se `usuario.troca_senha_obrigatoria = True`, exceto `PUT /me/senha` e
  `POST /auth/logout` (dependência alternativa `usuario_atual_permitindo_troca`). O login
  devolve o flag para o frontend redirecionar.
- **Rationale**: aplica a regra num único ponto, sem depender de cada rota lembrar.

## R8. Stack e ambiente

- **Decision**: Python 3.14 (venv atual), `uv` para dependências, FastAPI, Pydantic v2,
  pydantic-settings, SQLAlchemy 2.x **síncrono** com `psycopg` 3, Alembic, argon2-cffi,
  email-validator. Dev: pytest, httpx, ruff.
- **Rationale**: SQLAlchemy síncrono é mais simples (endpoints `def` rodam no threadpool do
  FastAPI) e sobra para o volume esperado. `uv` é o que o CLAUDE.md já usa nos comandos; ele
  precisa ser instalado (não está no PATH).
- **Alternatives considered**: SQLAlchemy async + asyncpg — mais complexidade de sessão e
  testes sem necessidade de desempenho.

## R9. PostgreSQL em dev e testes

- **Decision**: `docker-compose.yml` com `postgres:17`, dois bancos (`gerencia` e
  `gerencia_test`). A suíte roda `alembic upgrade head` uma vez no banco de teste e cada teste
  roda dentro de uma transação desfeita ao final (conexão com `join_transaction_mode=
  "create_savepoint"`).
- **Rationale**: a constituição exige PostgreSQL real nos testes de integração; Docker já está
  instalado. Rollback por teste mantém a suíte rápida e isolada.
- **Alternatives considered**: testcontainers (sobe um container por sessão de teste; mais
  lento e mais frágil no Windows); SQLite (proibido pela constituição).

## R10. Relógio

- **Decision**: domínio recebe `agora`/`hoje` como parâmetro. Serviços obtêm a hora de uma
  dependência `relogio` (UTC para timestamps; `America/Sao_Paulo` para "hoje"), sobrescrita
  nos testes.
- **Rationale**: Princípio III proíbe relógio implícito no domínio; torna testáveis bloqueio
  e expiração de sessão.

## R11. Formato de erro

- **Decision**: todas as respostas de erro seguem
  `{"erro": {"codigo": str, "mensagem": str, "campos": {campo: mensagem} | null}}`. Os 422 do
  Pydantic são convertidos para esse formato por um exception handler.
- **Rationale**: Princípio IV exige formato único e documentado.

## R12. Categoria "Salário" no cadastro (FR-018)

- **Decision**: esta feature cria a tabela `categoria` só com o necessário (`usuario_id`,
  `nome`, `tipo`, `ativa`, `sistema`) e insere "Salário" (`entrada`, `sistema = True`) na
  mesma transação do cadastro. A lista inicial das demais categorias fica para a feature de
  categorias.
- **Rationale**: a feature 001 depende da categoria de sistema existir para todo usuário;
  criar na mesma transação evita usuário sem "Salário". Nenhum campo além do necessário (P0).
