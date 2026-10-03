# Data Model: Atividade do Usuário (018)

## Nova tabela `evento_uso`

| Campo | Tipo | Regra |
| --- | --- | --- |
| `id` | bigint identity, PK | Ordem da linha do tempo e cursor da paginação |
| `usuario_id` | bigint, FK `usuario.id` `ON DELETE CASCADE` | Dono do evento; nunca o administrador |
| `tipo` | varchar(30), `CHECK tipo IN (...)` | Um dos tipos abaixo |
| `ocorrido_em` | timestamptz, `server_default now()` | Data e hora da ação |

Índice: `(usuario_id, id DESC)` para a linha do tempo, e `(ocorrido_em)` para a limpeza.

Não existe coluna de valor, descrição, nome ou id do registro afetado (FR-005), e nenhuma deve
ser acrescentada sem nova emenda.

### Tipos (lista fechada)

| Tipo | Gravado em | Rótulo no painel |
| --- | --- | --- |
| `conta_criada` | `auth.cadastrar` | Criou a conta |
| `login` | `auth.entrar` (só sucesso, só usuário comum) | Entrou no sistema |
| `senha_trocada` | `auth.trocar_senha` | Trocou a senha |
| `perfil_atualizado` | `perfil.atualizar_perfil` | Atualizou o perfil |
| `lancamento_criado` | `lancamento.criar_lancamento` | Lançou |
| `lancamento_editado` | `lancamento.editar_lancamento` | Editou lançamento |
| `lancamento_excluido` | `lancamento.excluir_lancamento` | Excluiu lançamento |
| `extrato_importado` | `importacao.confirmar` (um por confirmação) | Importou extrato |
| `categoria_criada` | `categoria.criar_categoria` | Criou categoria |
| `categoria_editada` | `categoria.editar_categoria` | Editou categoria |
| `recorrencia_criada` | `recorrencia.criar_recorrencia` | Criou recorrência |
| `recorrencia_editada` | `recorrencia.editar_recorrencia` | Editou recorrência |
| `divida_criada` | `divida.criar_divida` | Criou dívida |
| `cartela_criada` | `cartela.criar_cartela` | Criou cartela |
| `deposito_feito` | `cartela.depositar` | Depositou em cartela |
| `deposito_desfeito` | `cartela.desfazer_deposito` | Desfez depósito |
| `servico_criado` | `servico.criar_servico` | Criou serviço |
| `servico_editado` | `servico.editar_servico` | Editou serviço |
| `servico_excluido` | `servico.excluir_servico` | Excluiu serviço |
| `servico_recebido` | `servico.receber_servico` | Marcou serviço recebido |
| `recebimento_desfeito` | `servico.desfazer_recebimento` | Desfez recebimento |
| `lembrete_criado` | `lembrete.criar_livre` | Criou lembrete |
| `lembrete_editado` | `lembrete.editar_livre` (sem concluir) | Editou lembrete |
| `lembrete_concluido` | `lembrete.editar_livre` (`concluido` passa a `true`) | Concluiu lembrete |
| `lembrete_excluido` | `lembrete.excluir_livre` | Excluiu lembrete |
| `push_ativado` | `push.inscrever` | Ativou notificações |
| `push_removido` | `push.remover_inscricao` | Desativou notificações |

Regras:

- O evento só é gravado na mesma transação da ação bem-sucedida (research R1).
- Uma edição de lembrete que conclui grava só `lembrete_concluido`, mesmo que mude texto ou data
  junto. Isso é decidido por `domain/atividade.tipo_edicao_lembrete`.
- Retenção: eventos com `ocorrido_em < limite_retencao(agora)` são apagados pelo
  `limpar-eventos` (research R6).

## Alteração em `acao_admin`

- O `CHECK acao` passa a aceitar também `ver_atividade`.
- `ver_atividade` é gravada no máximo uma vez a cada 30 minutos por par administrador e conta
  (`domain/atividade.precisa_registrar_visita(ultima, agora)`).

## Derivados (não armazenados)

### Detalhe da conta

- **Conta**: `id`, `nome`, `email`, `criado_em`, `ativo` (os mesmos campos de `UsuarioAdminOut`).
- **Acesso**: `ultimo_acesso_em` (pode ser nulo, exibido como "nunca") e `sessoes_abertas`.
- **Contagens**: `lancamentos_manuais`, `lancamentos_importados`, `lancamentos_gerados`,
  `importacoes`, `recorrencias`, `dividas`, `cartelas`, `depositos`, `servicos`, `lembretes`,
  `aparelhos_push`. Todos são inteiros, com zero quando não há uso (regras em research R4).
- **Ações do administrador**: as últimas 50 sobre a conta, cada uma com `acao`, `ocorrida_em`
  e `admin_nome`.

### Página de eventos

`itens [{tipo, ocorrido_em}]`, até 50, do mais recente para o mais antigo, e `proximo` (id
para `?antes=`, ou `null` quando acabou).

## Migração

`0017_evento_uso.py`: cria `evento_uso` e índices e recria o `CHECK` de `acao_admin`. Se a 016
criar uma migração antes, usar o próximo número livre.
