# Contrato: Painel do Administrador

## Comando no servidor

```bash
uv run python -m app.cli criar-admin --nome "Admin" --email admin@exemplo.com \
  --telefone 11987654321 --cargo "Administrador"
```

Saída: `Administrador criado. Senha temporária (troque no primeiro login): <senha>`.
Erros (código de saída 1): administrador já existe; e-mail já cadastrado; dado inválido.

### Recuperar o acesso do administrador (emenda de 2026-09-29)

```bash
uv run python -m app.cli resetar-senha-admin
```

Gera nova senha temporária, encerra as sessões do administrador e exige troca no próximo login.
Saída: `Senha temporária do administrador (troque no próximo login): <senha>`.
Erro (código de saída 1): nenhum administrador cadastrado. Não entra no registro de ações
administrativas: é operação de quem opera o servidor, não do painel.

## Rotas (cookie `sessao` do administrador; formato único de erro)

Novo código: `acesso_negado` (403) para quem não é administrador.

### `GET /api/v1/admin/usuarios?busca=<texto>` → 200 `UsuarioAdminOut[]`

```json
[{ "id": 3, "nome": "Ana Souza", "email": "ana@exemplo.com", "criado_em": "2026-09-28T15:00:00Z" }]
```

Só contas de usuário comum, ordem alfabética; `busca` filtra nome ou e-mail sem diferenciar
maiúsculas.

### `POST /api/v1/admin/usuarios/{id}/reset-senha` → 200 `SenhaTemporariaOut`

```json
{ "senha_temporaria": "k3Jd9QpLm2Xa" }
```

Encerra as sessões do usuário, marca troca obrigatória e registra a ação. 404 `nao_encontrado`
se a conta não existe ou é do administrador.

Ambas: 401 sem sessão; 403 `troca_senha_obrigatoria` se o administrador ainda não trocou a
senha; 403 `acesso_negado` para usuário comum.
