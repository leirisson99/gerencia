# Research: Ciclo Aberto pelo Salário

Decisões técnicas da feature 001. Não há itens NEEDS CLARIFICATION pendentes. Duas decisões
de escopo foram tomadas com o usuário em 2026-09-28 (R1 e R2).

## R1. Categorias além de "Salário"

- **Decision**: todo usuário recebe uma lista inicial fixa de categorias no cadastro, além de
  "Salário": entrada "Renda extra"; saídas "Moradia", "Alimentação", "Transporte", "Saúde",
  "Lazer" e "Outros". Usuários já existentes recebem a mesma lista pela migração. A API só
  lista categorias (`GET /categorias`); criar, renomear e desativar ficam para uma feature
  própria.
- **Rationale**: a spec exige lançar gastos e entradas que não abrem ciclo (US1.3, US2), e o
  cadastro da 002 só cria "Salário". Uma lista inicial resolve sem abrir a frente de CRUD de
  categorias, que não tem spec. Decidido com o usuário.
- **Alternatives considered**: CRUD mínimo de categorias nesta feature (amplia escopo sem
  spec); lista inicial + criar (mesmo problema, menor).
- **Nota**: "Poupança" e "Cartão de crédito", citadas na constituição, entram com as features
  de cartela e de cartão, não agora (Princípio VI).

## R2. Escopo das histórias

- **Decision**: implementar US1–US4 (P1 e P2). As tarefas ficam agrupadas por história para
  permitir parar depois das P1.
- **Rationale**: FR-006, FR-008 e FR-010 são MUST na spec e dependem de US3/US4. Decidido com
  o usuário.

## R3. Derivação do ciclo

- **Decision**: funções puras em `app/domain/ciclo.py` que recebem as datas dos salários (em
  qualquer ordem, com repetição) e devolvem ciclos `Ciclo(inicio: date, fim: date | None)`.
  As datas são deduplicadas e ordenadas; cada ciclo vai de uma data até a véspera da seguinte;
  o último tem `fim = None`. Busca do ciclo de uma data por `bisect` sobre as datas ordenadas.
- **Rationale**: o Princípio II proíbe guardar ciclo. Um usuário lança ~12 salários por ano,
  então buscar todas as datas de salário a cada consulta é barato (uma consulta indexada) e
  mantém uma única fonte da verdade. Deduplicar resolve "dois salários na mesma data" sem
  ciclo de zero dias.
- **Alternatives considered**: tabela/visão materializada de ciclos (proibido); window
  function `LEAD()` no SQL (tira a regra do domínio e dificulta testar casos-limite).

## R4. Quem é salário

- **Decision**: um lançamento é salário quando sua categoria é a de sistema "Salário"
  (`categoria.sistema = true` e `nome = 'Salário'`) e o `status` é `realizado`. A categoria
  "Salário" só aceita `status = realizado`; enviar `previsto` é recusado com erro de campo.
- **Rationale**: FR-002 fala em "entrada, realizado, na categoria Salário". Proibir salário
  previsto evita um lançamento na categoria que abre ciclo mas não abre, uma ambiguidade sem
  uso no MVP (o salário não é recorrência).

## R5. Tipo do lançamento

- **Decision**: o cliente não envia `tipo`. O serviço copia `categoria.tipo` para
  `lancamento.tipo` ao criar e ao trocar a categoria.
- **Rationale**: a constituição limita os campos obrigatórios a valor, categoria e data
  (Princípio VI). Derivar o tipo da categoria elimina a combinação inválida "saída em
  Salário". A coluna fica guardada porque o saldo (feature da tela do ciclo) soma por tipo.

## R6. Regra de cobertura (nenhum lançamento fora de ciclo)

- **Decision**: uma única regra pura, `verificar_cobertura(datas_salario, menor_data_outros)`,
  valida o estado **depois** de qualquer escrita (criar, editar, excluir, trocar categoria):
  1. sem salários e com outros lançamentos → `salario_necessario`;
  2. menor data dos outros lançamentos antes do primeiro salário → `antes_do_primeiro_ciclo`
     (ao criar/editar o próprio lançamento) ou `lancamentos_sem_ciclo` (quando a mudança é
     num salário e afeta outros lançamentos).
  O serviço monta o estado resultante (datas de salário e menor data dos demais) e chama a
  regra antes de gravar.
- **Rationale**: FR-005, FR-006, US4.3 e os casos-limite de troca de categoria são o mesmo
  invariante: "toda data de lançamento ≥ primeiro salário". Uma regra só evita que cada
  endpoint reimplemente a checagem.
- **Alternatives considered**: checagens separadas por endpoint (duplicação, fácil esquecer um
  caso); trigger no banco (regra fora do domínio, difícil de testar).

## R7. Concorrência

- **Decision**: toda escrita de lançamento começa com `SELECT ... FROM usuario WHERE id = :id
  FOR UPDATE`, serializando as escritas do mesmo usuário na transação.
- **Rationale**: sem isso, excluir o único salário e lançar um gasto ao mesmo tempo poderiam
  passar na checagem de cobertura e deixar um gasto sem ciclo (viola SC-005). O bloqueio é por
  usuário, então usuários diferentes não se esperam.
- **Alternatives considered**: isolamento `SERIALIZABLE` com retry (mais código e mais erros
  transitórios); advisory lock (mesmo efeito, menos explícito).

## R8. Salário no futuro

- **Decision**: `data > relogio.hoje_sp()` em lançamento de salário (criar, editar, ou trocar
  para a categoria "Salário") é recusado com erro de campo em `data`. Outros lançamentos podem
  ter data futura (previstos, feature de recorrências), desde que caiam num ciclo; como o
  ciclo aberto não tem fim, qualquer data futura cai nele.
- **Rationale**: FR-004; o relógio injetado mantém a regra testável.

## R9. Dinheiro na API

- **Decision**: `valor` é `StrictInt` com `gt=0` e `le=99_999_999_999` (R$ 999.999.999,99);
  coluna `BIGINT` com `CHECK (valor > 0)`. JSON com `10.5` ou `"1000"` é recusado.
- **Rationale**: Princípio I (centavos `int`, nunca float). O limite evita estouro e erro de
  digitação absurdo sem restringir uso real.

## R10. Categoria inexistente ou de outro usuário

- **Decision**: `categoria_id` que não existe ou pertence a outro usuário responde **404
  `nao_encontrado`**, a mesma resposta nos dois casos. Categoria inativa responde 422 com
  erro no campo `categoria_id`.
- **Rationale**: Princípio V exige 404 para dado de outro usuário; responder igual para
  "inexistente" não revela que o id existe.

## R11. Sugestão do valor do salário (FR-012)

- **Decision**: `GET /salarios/sugestao` devolve `{"valor": <int> | null}` com o valor do
  salário de data mais recente (desempate pelo maior id).
- **Rationale**: FR-012 é SHOULD e barato; um endpoint próprio mantém o formulário do
  cliente simples.

## R12. Geração de previstos ao abrir ciclo (FR-011)

- **Decision**: nada é implementado nesta feature. A feature de recorrências vai chamar sua
  geração a partir do serviço de lançamentos quando um salário abrir ciclo.
- **Rationale**: a regra está explicitamente adiada para a spec de recorrências; criar um
  gancho vazio agora seria "preparar para o futuro" (Princípio VI).

## R13. Listagem por ciclo

- **Decision**: `GET /ciclos/{data}/lancamentos` lista os lançamentos do ciclo que contém a
  data, ordenados por data e id. Sem paginação (um ciclo tem dezenas de lançamentos).
- **Rationale**: é a forma verificável pela API de FR-007 e US4.1 ("os lançamentos passam a
  pertencer ao ciclo em que sua data cai"). Saldo e gasto por categoria continuam fora (tela
  do ciclo).
