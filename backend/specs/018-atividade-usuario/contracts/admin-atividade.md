# Contrato: atividade da conta (018)

Rotas novas no router `/api/v1/admin`, só para o administrador (`AdministradorDep`). Erros no
formato único `ErroOut`:

- `401`: sem sessão;
- `403 acesso_negado`: usuário comum, inclusive para a própria conta;
- `404 nao_encontrado`: conta inexistente ou do próprio administrador.

As mudanças são aditivas; as rotas existentes não mudam.

## GET `/api/v1/admin/usuarios/{usuario_id}`

Registra `ver_atividade` (janela de 30 min). Responde `DetalheContaOut`:

```json
{
  "conta": {
    "id": 7,
    "nome": "Ana",
    "email": "ana@exemplo.com",
    "criado_em": "2026-09-28T13:00:00-03:00",
    "ativo": true
  },
  "ultimo_acesso_em": "2026-10-02T08:10:00-03:00",
  "sessoes_abertas": 2,
  "contagens": {
    "lancamentos_manuais": 5,
    "lancamentos_importados": 3,
    "lancamentos_gerados": 4,
    "importacoes": 1,
    "recorrencias": 2,
    "dividas": 0,
    "cartelas": 1,
    "depositos": 2,
    "servicos": 0,
    "lembretes": 1,
    "aparelhos_push": 1
  },
  "acoes_admin": [
    {
      "acao": "reset_senha",
      "ocorrida_em": "2026-10-01T10:00:00-03:00",
      "admin_nome": "Administrador"
    }
  ]
}
```

- `ultimo_acesso_em` pode vir `null` quando não há acesso registrado.
- `acao` é um destes valores: `reset_senha`, `desativar_conta`, `reativar_conta` ou
  `ver_atividade`. A lista traz no máximo 50 itens, da ação mais recente para a mais antiga.
- Nenhum campo é valor monetário, texto digitado pelo usuário, telefone, cargo ou data de
  nascimento.

## GET `/api/v1/admin/usuarios/{usuario_id}/eventos?antes={id}`

Também registra `ver_atividade` (mesma janela). `antes` é opcional e precisa ser um inteiro
positivo (senão a resposta é `422`). Responde `PaginaEventosOut`:

```json
{
  "itens": [
    { "tipo": "extrato_importado", "ocorrido_em": "2026-10-02T09:12:30-03:00" },
    { "tipo": "login", "ocorrido_em": "2026-10-02T09:10:02-03:00" }
  ],
  "proximo": 1834
}
```

- `itens` traz até 50 eventos, do mais recente para o mais antigo. `tipo` é um dos valores de
  [data-model.md](../data-model.md).
- `proximo` é o valor de `antes` para pedir a página seguinte; vem `null` quando não há mais
  eventos.
- Não há `id` nos itens nem nada que aponte para o registro afetado.

## Efeitos colaterais nas rotas existentes

Nenhuma resposta muda. As ações bem-sucedidas listadas em [data-model.md](../data-model.md)
passam a gravar um evento de uso na mesma transação.

## CLI

`python -m app.cli limpar-eventos`: apaga os eventos com mais de 12 meses. Imprime só
`removidos=<n>`.
