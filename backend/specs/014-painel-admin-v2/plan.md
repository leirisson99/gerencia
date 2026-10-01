# Implementation Plan: Painel do Administrador v2

**Branch**: `014-painel-admin-v2` | **Date**: 2026-09-30 | **Spec**: [spec.md](spec.md)

## Summary

Coluna `usuario.ativo` (migração `0014`) e duas ações novas em `acao_admin`
(`desativar_conta`, `reativar_conta`). Rotas `POST /admin/usuarios/{id}/desativar` e
`/reativar`; `GET /admin/usuarios` ganha `ativo` e `?situacao=`. `GET /admin/resumo` faz uma
consulta agregada por bloco; a montagem dos 12 meses e o ranking das formas são funções puras
em `domain/painel.py`. O login confere `ativo` depois da senha.

## Contrato

| Método | Rota | Resposta |
| --- | --- | --- |
| GET | `/api/v1/admin/usuarios?busca=&situacao=ativos\|desativados` | `UsuarioAdminOut[]` (+ `ativo`) |
| POST | `/api/v1/admin/usuarios/{id}/desativar` | `UsuarioAdminOut`; 404 |
| POST | `/api/v1/admin/usuarios/{id}/reativar` | `UsuarioAdminOut`; 404 |
| GET | `/api/v1/admin/resumo` | `ResumoAdminOut` |
| POST | `/api/v1/auth/login` | novo erro 403 `conta_desativada` |

`ResumoAdminOut`: `contas {total, ativas, desativadas}`, `lancamentos {total, realizados,
previstos}`, `por_mes [{mes: "AAAA-MM", entradas, saidas}]` (12, do mais antigo ao atual),
`dividas_por_forma [{forma, quantidade}]` (as 4 formas, mais usada primeiro). Só inteiros de
contagem. Mudanças aditivas, sem quebra de contrato.

## US4 — mais indicadores (constituição 5.2.0)

Migração `0016`: `usuario.ultimo_acesso_em` (timestamptz, nulo). Atualizado em
`criar_sessao` (login e cadastro) e em `resolver_sessao`, só quando
`domain/painel.precisa_registrar_acesso` diz que o dia em São Paulo mudou — no máximo uma
escrita por conta por dia. `ResumoAdminOut` ganha, de forma aditiva:

- `cadastros_por_mes [{mes, quantidade}]` (12 meses, mesma janela do `por_mes`);
- `engajamento {ativas_7_dias, ativas_30_dias, com_lancamento}`;
- `lancamentos.importados` e `lancamentos.manuais` (`id_externo` preenchido ou não);
- `uso_funcionalidades [{funcionalidade, contas}]` para `recorrencias`, `dividas`, `cartelas`,
  `servicos` e `importacao` (contas distintas, ordem fixa);
- `por_tipo_renda {clt, prestador, clt_prestador}`.

Cada bloco é uma consulta agregada; nada sai por conta. `UsuarioAdminOut` não muda.

## Constitution Check (5.0.0)

| Princípio | Verificação | Status |
| --- | --- | --- |
| I. Integridade financeira | Nenhum valor lido ou alterado; desativar não toca dados financeiros. | ✅ |
| II. Ciclo | Não muda. | ✅ |
| III. Teste primeiro | `domain/painel.py` e as rotas testados antes. | ✅ |
| IV. Contratos | Schemas tipados; erros no formato único. | ✅ |
| V. Isolamento | Exatamente o que a emenda 5.0.0 permite: situação da conta, contagens globais sem valores nem usuário; ações registradas. Teste garante a ausência de valores e ids. | ✅ |
| VI. Escopo | Pedido explícito; sem papéis novos. | ✅ |
