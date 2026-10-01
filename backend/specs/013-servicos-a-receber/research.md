# Research: Serviços a Receber

## 1. Como ligar serviço e lançamento

- **Decision**: `servico.lancamento_id` (FK única, obrigatória, `ON DELETE RESTRICT`) e
  `Lancamento.servico_id` como `column_property`.
- **Rationale**: mesmo padrão já usado por `casa.lancamento_id`/`cartela_id`; não mexe na tabela
  `lancamento` nem nos seus `CHECK`s de parcela.
- **Alternatives considered**: `lancamento.servico_id` (coluna nova numa tabela grande e central);
  reusar `divida` com `me_devem` e 1 parcela (semântica errada: exige forma de pagamento, dia de
  vencimento e pessoa, e o recebimento com valor diferente não cabe).

## 2. Onde guardar o valor recebido

- **Decision**: no lançamento (realizado); o serviço guarda só o valor combinado.
- **Rationale**: o saldo sempre vem do lançamento (Princípio I); desfazer recupera o combinado
  sem guardar estado extra.
- **Alternatives considered**: coluna `valor_recebido` no serviço (dado duplicado que pode
  divergir do lançamento).

## 3. Situação derivada

- **Decision**: `situacao(status_lancamento, data_prevista, hoje)` em `domain/servico.py`;
  listagem filtra em Python.
- **Rationale**: constituição exige situação derivada; volume por usuário é pequeno.
- **Alternatives considered**: filtro em SQL com `CASE` (duplica a regra fora do domínio).

## 4. Trava do lançamento

- **Decision**: em `editar_lancamento`, recusar mudança de valor, status, categoria e data de
  lançamento de serviço (422 no campo, "Altere pelo serviço."); em `excluir_lancamento`, 409
  `lancamento_de_servico`. Só vale se o dono tem acesso a serviços.
- **Rationale**: evita divergência entre serviço e lançamento (SC-004); sem acesso a serviços, o
  usuário `clt` não teria como corrigir, então o lançamento vira normal.
- **Alternatives considered**: permitir e sincronizar de volta no serviço (dois caminhos para a
  mesma mudança).

## 5. Acesso por tipo de renda

- **Decision**: dependência `ComServicosDep` nas rotas de serviço → 403 `perfil_sem_servicos`.
- **Rationale**: regra de acesso, não de negócio; uma dependência cobre todas as rotas.
- **Alternatives considered**: checar em cada service (repetição).

## 6. Descrição do lançamento gerado

- **Decision**: `cliente` ou `cliente — descrição`, cortada em 200 caracteres.
- **Rationale**: o lançamento aparece em listas e no calendário sem precisar abrir o serviço.
