# Data Model: Cadastro e Login de Usuários

Todos os timestamps são `timestamptz` em UTC. `data_nascimento` é `date`. Toda mudança de
schema vem numa migração Alembic reversível.

## usuario

| Campo | Tipo | Regras |
| --- | --- | --- |
| id | bigint, PK | identity |
| nome | varchar(120) | obrigatório, sem espaços nas pontas, não vazio |
| email | varchar(254) | obrigatório, normalizado (minúsculo, sem espaços), **UNIQUE** |
| senha_hash | varchar(255) | argon2id; nunca sai da API |
| telefone | varchar(11) | só dígitos, 10 ou 11; DDD 11–99; com 11 dígitos começa com 9 |
| cargo | varchar(80) | obrigatório, texto livre, informativo |
| data_nascimento | date, null | entre 1900-01-01 e hoje (São Paulo) |
| papel | varchar(10) | `usuario` \| `admin`, CHECK; cadastro público sempre `usuario` |
| troca_senha_obrigatoria | boolean | default `false` |
| criado_em | timestamptz | default now() |
| atualizado_em | timestamptz | atualizado em toda alteração de perfil ou senha |

**Transições**:
- `troca_senha_obrigatoria`: `false → true` só pela feature 003 (reset); `true → false` ao
  concluir a troca de senha.
- `papel`: não muda nesta feature.

## sessao

| Campo | Tipo | Regras |
| --- | --- | --- |
| id | bigint, PK | identity |
| usuario_id | bigint, FK → usuario.id | ON DELETE CASCADE, indexado |
| token_hash | char(64) | SHA-256 hex do token, **UNIQUE** |
| criada_em | timestamptz | default now() |
| ultimo_uso_em | timestamptz | atualizado a cada requisição autenticada |

**Regras**:
- Válida se `agora − ultimo_uso_em < 30 dias`. Sessão vencida é apagada ao ser encontrada.
- Logout apaga a sessão atual.
- Troca de senha apaga todas as sessões do usuário exceto a atual.

## tentativa_login

| Campo | Tipo | Regras |
| --- | --- | --- |
| id | bigint, PK | identity |
| email_normalizado | varchar(254) | indexado junto com `ocorrida_em`; **sem FK** (e-mail pode não existir) |
| ocorrida_em | timestamptz | hora da falha |

**Regras** (função pura em `domain/login.py`, ver research R4):
- 5 falhas numa janela de 15 min → bloqueado até a 5ª falha + 15 min.
- Login bem-sucedido apaga as falhas do e-mail.
- Falhas com mais de 24 h são apagadas no fluxo de login.

## categoria (mínima, para FR-018)

| Campo | Tipo | Regras |
| --- | --- | --- |
| id | bigint, PK | identity |
| usuario_id | bigint, FK → usuario.id | ON DELETE CASCADE, indexado |
| nome | varchar(60) | obrigatório |
| tipo | varchar(7) | `entrada` \| `saida`, CHECK |
| ativa | boolean | default `true` |
| sistema | boolean | default `false`; categoria protegida contra exclusão/renomeação |

**Regras**:
- Índice único parcial: um único registro `sistema = true AND nome = 'Salário'` por
  `usuario_id`.
- Criada na mesma transação do cadastro: `("Salário", "entrada", sistema = true)`.
- Demais categorias e as regras de edição ficam na feature de categorias.

## Relacionamentos

```text
usuario 1 ── N sessao
usuario 1 ── N categoria
tentativa_login (independente, por e-mail)
```
