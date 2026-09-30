# Research: Tipo de Renda e Ciclo Mensal do Prestador

## 1. Onde decidir a regra de ciclo

- **Decision**: funções `ciclo_da_data_do_usuario` / `ciclo_atual_do_usuario` em
  `services/ciclo.py`, que leem `usuario.tipo_renda` e chamam `domain/ciclo.py`.
- **Rationale**: hoje seis pontos montam o ciclo direto de `datas_de_salario` (limite,
  recorrência, lançamento, importação, resumo, rotas). Centralizar evita que um deles esqueça o
  prestador.
- **Alternatives considered**: passar o tipo por parâmetro em todos os services (espalha a
  decisão); estratégia/objeto de regra injetado (mais código sem ganho no monólito).

## 2. Como marcar o mês atual como aberto

- **Decision**: campo `mes_atual: bool = False` em `Ciclo`; `aberto` vira
  `fim is None or mes_atual`.
- **Rationale**: o mês atual tem `fim` definido (último dia), mas precisa aparecer como aberto.
  O padrão `False` mantém todas as construções e testes existentes.
- **Alternatives considered**: `fim = None` no mês atual (lançamentos futuros do mês seguinte
  entrariam no mês atual); trocar `aberto` por campo obrigatório (quebra testes do CLT).

## 3. Vizinhos do mês

- **Decision**: `anterior` só se houver lançamento do usuário antes do início do mês; `proximo`
  só se o mês seguinte não for posterior ao mês atual.
- **Rationale**: evita navegação infinita para trás e para frente; espelha o CLT, onde não há
  ciclo antes do primeiro salário nem depois do atual.
- **Alternatives considered**: sempre ter anterior (navegação sem fim no frontend); limitar pela
  data de cadastro (a pessoa pode lançar coisas de antes do cadastro).

## 4. Geração dos previstos do mês

- **Decision**: `garantir_previstos_do_mes` idempotente, chamada em `GET /ciclos/atual`,
  `GET /ciclos/{data}/resumo`, `POST /lancamentos` e `POST /recorrencias`; trava a linha do
  usuário (`travar_escritas`) antes de gerar.
- **Rationale**: no prestador nenhum evento abre o mês. `gerar_previstos` já pula recorrências
  com lançamento no ciclo; o lock evita duplicar com requisições simultâneas.
- **Alternatives considered**: job agendado na virada do mês (serviço extra, contra o Princípio
  VI); gerar sob demanda sem gravar (previsto não teria id para ser confirmado).

## 5. `abre_ciclo` do lançamento

- **Decision**: `column_property` `tipo_renda_usuario` no `Lancamento` (subconsulta escalar,
  igual a `cartela_id`) e `abre_ciclo` considerando o tipo.
- **Rationale**: o schema `LancamentoOut` lê `abre_ciclo` direto do modelo; para o prestador
  precisa ser `false` sem mudar as rotas.
- **Alternatives considered**: relacionamento `usuario` (N+1 em listagens); calcular no schema
  com contexto (Pydantic sem acesso ao tipo).

## 6. Troca de `prestador` para `clt*`

- **Decision**: função pura `verificar_troca_tipo_renda(atual, novo, datas_salario,
  menor_data_outros, salario_irregular)` que devolve `ProblemaTroca`: `SALARIO_INVALIDO` (há
  "Salário" previsto ou futuro) antes de `LANCAMENTOS_SEM_CICLO` (reusa `verificar_cobertura`).
- **Rationale**: o prestador pode ter lançado "Salário" previsto/futuro; como CLT isso violaria
  as regras do salário. Reusar a cobertura garante SC-004.
- **Alternatives considered**: converter salários irregulares automaticamente (muda dado do
  usuário sem confirmação).
