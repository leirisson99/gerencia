# Data Model: Lembretes por Push

Migração `0015_lembretes_push`, reversível. Todas as tabelas têm `usuario_id` com `ON DELETE
CASCADE`.

## Tabelas

### `lembrete` (lembrete livre)

| Campo | Tipo | Regras |
| --- | --- | --- |
| id | bigint identity | PK |
| usuario_id | bigint FK `usuario` | obrigatório |
| texto | varchar(200) | obrigatório; aparado; não vazio |
| data | date | obrigatória; passada ou futura |
| concluido_em | timestamptz | `null` enquanto pendente |
| criado_em | timestamptz | default now |

Índice `(usuario_id, data)`.

### `inscricao_push` (aparelho autorizado)

| Campo | Tipo | Regras |
| --- | --- | --- |
| id | bigint identity | PK |
| usuario_id | bigint FK `usuario` | obrigatório |
| endpoint | text | obrigatório, **único** na tabela; URL `https://`, até 2048 caracteres |
| p256dh | varchar(200) | chave pública do navegador (base64url) |
| auth | varchar(100) | segredo de autenticação (base64url) |
| criado_em | timestamptz | default now |

Índice `(usuario_id)`.

### `envio_lembrete` (resumo do dia já enviado)

| Campo | Tipo | Regras |
| --- | --- | --- |
| usuario_id | bigint FK `usuario` | PK composta |
| dia | date | PK composta; dia em `America/Sao_Paulo` |
| enviado_em | timestamptz | default now |

## Derivados (sem tabela)

### Pendência de lançamento

Lançamentos do usuário com `status = previsto` e `data <= hoje + 3`:

- **conta a pagar**: `tipo = saida` e `conta_no_saldo = true`;
- **valor a receber**: `tipo = entrada`.

### Situação (função pura `situacao(data, hoje)`)

| Condição | Situação |
| --- | --- |
| `data < hoje` | `atrasado` |
| `hoje <= data <= hoje + 3` | `a_vencer` |
| `data > hoje + 3` | fora da janela (`None`) |

Lembrete livre entra na janela só se `concluido_em is null`.

## Resumo da notificação (função pura `texto_resumo(contagem, hoje)`)

`Contagem`: contas, valores e livres, cada um com `atrasados` e `a_vencer`. Total zero → `None`
(sem push).

- Título: `Gerencia`.
- Corpo: partes não vazias, nesta ordem, unidas por ` · `, terminando com ponto:
  1. contas: `N conta(s) a pagar` + sufixo;
  2. valores: `N valor(es) a receber` + sufixo;
  3. livres: `N lembrete(s)` + sufixo.
- Sufixo de cada parte:
  - Só atrasados: `, atrasada(s)` para contas; `, atrasado(s)` para valores e lembretes.
  - Só a vencer: ` até <dia>`.
  - Os dois: ` até <dia> (A atrasada(s))`, com o gênero da parte.
- `<dia>` é o dia da semana de `hoje + 3` em português, sem "-feira": segunda, terça, quarta,
  quinta, sexta, sábado, domingo.

Exemplos, com hoje = quarta-feira e o fim da janela no sábado:

- 2 contas a vencer e 1 valor atrasado: `2 contas a pagar até sábado · 1 valor a receber,
  atrasado.`
- 3 contas (1 atrasada) e 1 lembrete: `3 contas a pagar até sábado (1 atrasada) · 1 lembrete
  até sábado.`

## Transições

- Lembrete livre:
  - pendente → concluído: `PATCH concluido=true` grava `concluido_em = agora`.
  - concluído → pendente: `PATCH concluido=false` grava `concluido_em = null`.
- Inscrição:
  - O `PUT` cria a inscrição ou transfere para quem chamou, atualizando as chaves.
  - O `DELETE` ou uma recusa 404/410 no envio apaga a inscrição.
- Envio do dia:
  - Antes de enviar, a reserva cria a linha.
  - Se nenhum aparelho recebeu, a linha é apagada. Se algum recebeu, ela fica.
