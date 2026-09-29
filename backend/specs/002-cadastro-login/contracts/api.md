# Contrato da API: Cadastro e Login

Base: `/api/v1`. Corpo sempre JSON. Requisições que alteram estado exigem
`Content-Type: application/json`. A autenticação é o cookie `sessao` (HttpOnly, SameSite=Lax).
O OpenAPI gerado pelo FastAPI é o contrato final; este documento é a referência de desenho.

## Formato de erro (todas as rotas)

```json
{
  "erro": {
    "codigo": "validacao",
    "mensagem": "Dados inválidos.",
    "campos": { "telefone": "Informe DDD e número, com 10 ou 11 dígitos." }
  }
}
```

| Código | HTTP | Quando |
| --- | --- | --- |
| `validacao` | 422 | campo faltando ou inválido; `campos` preenchido |
| `email_ja_cadastrado` | 409 | cadastro com e-mail existente |
| `credenciais_invalidas` | 401 | login com e-mail ou senha errados (mensagem genérica) |
| `login_bloqueado` | 429 | 5 falhas em 15 min; header `Retry-After` em segundos |
| `nao_autenticado` | 401 | sem cookie, sessão inexistente ou expirada |
| `troca_senha_obrigatoria` | 403 | conta marcada; só troca de senha e logout liberados |
| `senha_atual_incorreta` | 400 | troca de senha com a senha atual errada |
| `nao_encontrado` | 404 | recurso de outro usuário ou inexistente |
| `tipo_conteudo_invalido` | 415 | corpo enviado sem `Content-Type: application/json` |

## Schemas

**UsuarioOut**

```json
{
  "id": 1,
  "nome": "Ana Souza",
  "email": "ana@exemplo.com",
  "telefone": "11987654321",
  "cargo": "Desenvolvedora",
  "data_nascimento": "1995-03-15",
  "troca_senha_obrigatoria": false,
  "criado_em": "2026-09-28T22:00:00Z"
}
```

`senha_hash` e `papel` nunca aparecem.

## Rotas

### `GET /health` (pública)

200 `{"status": "ok"}`.

### `POST /api/v1/auth/cadastro` (pública)

Entrada:

```json
{
  "nome": "Ana Souza",
  "email": "ana@exemplo.com",
  "telefone": "(11) 98765-4321",
  "cargo": "Desenvolvedora",
  "senha": "segredo123",
  "data_nascimento": null
}
```

- 201 → `UsuarioOut` + `Set-Cookie: sessao=...` (já entra logado). Cria a categoria "Salário".
- 409 `email_ja_cadastrado`; 422 `validacao`.
- Campos extras (ex.: `papel`) → 422.

### `POST /api/v1/auth/login` (pública)

Entrada: `{"email": "...", "senha": "..."}`

- 200 → `UsuarioOut` + `Set-Cookie`. Se `troca_senha_obrigatoria = true`, o frontend
  redireciona para a troca de senha.
- 401 `credenciais_invalidas`; 429 `login_bloqueado`.

### `POST /api/v1/auth/logout` (autenticada, liberada com troca obrigatória)

- 204, apaga a sessão atual e o cookie.

### `GET /api/v1/me` (autenticada)

- 200 → `UsuarioOut`. 401; 403 `troca_senha_obrigatoria`.

### `PATCH /api/v1/me` (autenticada)

Entrada (todos opcionais; enviar `data_nascimento: null` remove a data):

```json
{ "nome": "Ana S.", "telefone": "11912345678", "cargo": "Tech lead", "data_nascimento": null }
```

- 200 → `UsuarioOut`. `email` ou qualquer campo desconhecido → 422. Mesmas validações do
  cadastro. 401; 403 `troca_senha_obrigatoria`.

### `PUT /api/v1/me/senha` (autenticada, liberada com troca obrigatória)

Entrada: `{"senha_atual": "...", "nova_senha": "..."}`

- 204. Remove `troca_senha_obrigatoria` e apaga as outras sessões do usuário.
- 400 `senha_atual_incorreta`; 422 `validacao` (senha fraca ou igual à atual); 401.

## Isolamento

Nenhuma rota desta feature recebe id de usuário: tudo é do usuário da sessão. Os testes de
API garantem que a sessão de A nunca devolve nem altera dados de B.
