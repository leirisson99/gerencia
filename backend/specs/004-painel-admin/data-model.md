# Data Model: Painel do Administrador

Migração reversível `0004_acao_admin`.

## usuario (existente)

- Novo índice único parcial `uq_usuario_admin_unico` em `(papel)` onde `papel = 'admin'`: no
  máximo um administrador.

## acao_admin (nova)

| Campo | Tipo | Regras |
| --- | --- | --- |
| id | bigint, PK | identity |
| admin_id | bigint, FK `usuario.id` | `ON DELETE CASCADE` |
| acao | varchar(30) | CHECK `acao IN ('reset_senha')` |
| usuario_alvo_id | bigint, FK `usuario.id` | `ON DELETE CASCADE` |
| ocorrida_em | timestamptz | hora da ação |

Índice em `usuario_alvo_id`.
