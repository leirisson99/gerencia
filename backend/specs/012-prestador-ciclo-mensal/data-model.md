# Data Model: Tipo de Renda e Ciclo Mensal do Prestador

## usuario (alterada)

| Campo | Tipo | Regras |
| --- | --- | --- |
| tipo_renda | `VARCHAR(13) NOT NULL DEFAULT 'clt'` | `CHECK (tipo_renda IN ('clt','prestador','clt_prestador'))`; contas existentes recebem `clt` |

Migração `0012_tipo_renda.py`: `add_column` com `server_default` e o `CHECK`; `downgrade`
remove os dois.

## lancamento (sem mudança de schema)

- `tipo_renda_usuario` (`column_property`, só leitura): tipo de renda do dono do lançamento.
- `abre_ciclo` = categoria é "Salário" de sistema **e** status realizado **e** tipo de renda
  diferente de `prestador`.

## Ciclo (derivado, `domain/ciclo.py`)

| Campo | Salário (`clt`, `clt_prestador`) | Mês (`prestador`) |
| --- | --- | --- |
| inicio | data do salário | dia 1 do mês |
| fim | véspera do próximo salário; `None` no último | último dia do mês |
| anterior | início do ciclo anterior | dia 1 do mês anterior, se houver lançamento antes de `inicio` |
| proximo | início do próximo ciclo | dia 1 do mês seguinte, se não for posterior ao mês atual |
| mes_atual | `False` | `inicio` é o dia 1 do mês de hoje |
| aberto (propriedade) | `fim is None` | `mes_atual` |

## Troca de tipo de renda (derivada, `domain/ciclo.py`)

| De → Para | Resultado |
| --- | --- |
| mesmo tipo | aceita |
| `clt` ↔ `clt_prestador` | aceita |
| `clt*` → `prestador` | aceita |
| `prestador` → `clt*` | `SALARIO_INVALIDO` se houver "Salário" previsto ou com data > hoje; senão `LANCAMENTOS_SEM_CICLO` se `verificar_cobertura` acusar problema; senão aceita |
