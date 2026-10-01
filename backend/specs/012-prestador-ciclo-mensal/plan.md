# Implementation Plan: Tipo de Renda e Ciclo Mensal do Prestador

**Branch**: `012-prestador-ciclo-mensal` | **Date**: 2026-09-30 | **Spec**: [spec.md](spec.md)

## Summary

Coluna `usuario.tipo_renda` (`clt` | `prestador` | `clt_prestador`, padrão `clt`), opcional no
cadastro, devolvida no `/me` e editável no `PATCH /me`. A decisão "qual regra de ciclo" passa a
viver num único ponto de `services/ciclo.py`, que escolhe entre os ciclos de salário (regra
atual) e o novo ciclo mensal (`domain/ciclo.py: ciclo_mensal`). Para o prestador, a cobertura de
ciclo e as regras do salário deixam de ser aplicadas em lançamentos, dívidas, cartelas e
importação; os previstos das recorrências do mês são gerados de forma idempotente ao consultar o
ciclo atual ou o resumo e ao criar lançamento ou recorrência. A troca de tipo de renda é validada
por uma função pura. `clt_prestador` se comporta como `clt` nesta feature.

## Technical Context

**Language/Version**: Python 3.14

**Primary Dependencies**: as mesmas (FastAPI, SQLAlchemy 2, Pydantic v2, Alembic)

**Storage**: PostgreSQL 17 — coluna `usuario.tipo_renda VARCHAR(13) NOT NULL DEFAULT 'clt'`,
`CHECK (tipo_renda IN ('clt','prestador','clt_prestador'))` (migração `0012`)

**Testing**: `tests/domain/test_ciclo.py` (ciclo mensal), `tests/domain/test_usuario.py` (tipos e
troca); `tests/api/test_prestador.py` (novo) e ajustes em `test_cadastro.py`, `test_perfil.py`

**Project Type**: web service (só backend nesta feature)

**Performance Goals**: sem consulta extra relevante para `clt`; para `prestador`, uma consulta
de `min(data)` para o anterior do mês e a geração idempotente de previstos (sob o lock de
escrita do usuário)

**Constraints**: nenhum teste existente do fluxo CLT pode mudar (SC-002)

## Constitution Check

| Princípio | Verificação | Status |
| --- | --- | --- |
| I. Integridade financeira | Nada muda nos cálculos: saldo, gasto por categoria e limite usam o mesmo filtro, só o intervalo do ciclo muda. Sem float. | ✅ |
| II. Ciclo derivado do tipo de renda | Ciclo mensal derivado da data; nada guardado; `clt`/`clt_prestador` com a regra atual; troca `prestador → clt*` validada (cobertura + salário realizado e não futuro). | ✅ |
| III. Teste primeiro | `ciclo_mensal`, `ciclo_pelo_mes` e `verificar_troca_tipo_renda` em `domain/`, testadas antes, com fevereiro 28/29, 30/31 dias, virada de ano, dia 1, último dia e mês futuro. | ✅ |
| IV. Contratos | `tipo_renda` como `Literal` em `CadastroIn`, `PerfilIn` e `UsuarioOut`; mudanças aditivas; novo erro 409 `salario_invalido` na troca; registrados em [contracts/api.md](contracts/api.md). | ✅ |
| V. Isolamento | `tipo_renda` só no `/me` do próprio usuário; o schema do administrador não muda. | ✅ |
| VI. Escopo | Pedido explícito (spec, Assumptions). Serviços a receber ficam na 013. Nenhum campo obrigatório novo em lançamento; `tipo_renda` é opcional no cadastro. | ✅ |

**Resultado**: sem violações. Reavaliado após o desenho: sem mudanças.

## Project Structure

### Documentation

```text
specs/012-prestador-ciclo-mensal/
├── plan.md, research.md, data-model.md, quickstart.md
├── contracts/api.md
└── tasks.md            # /speckit-tasks
```

### Source Code

```text
backend/
├── alembic/versions/0012_tipo_renda.py
├── app/domain/usuario.py           # TIPOS_RENDA, ciclo_pelo_mes
├── app/domain/ciclo.py             # Ciclo.mes_atual, ciclo_mensal, ProblemaTroca, verificar_troca_tipo_renda
├── app/models/usuario.py           # + tipo_renda
├── app/models/lancamento.py        # + tipo_renda_usuario (column_property); abre_ciclo considera o tipo
├── app/schemas/usuario.py          # tipo_renda em CadastroIn, PerfilIn, UsuarioOut
├── app/services/auth.py            # grava tipo_renda no cadastro
├── app/services/ciclo.py           # travar_escritas devolve o tipo; ciclo_da_data_do_usuario / ciclo_atual_do_usuario
├── app/services/recorrencia.py     # garantir_previstos_do_mes; criar_recorrencia usa o ciclo do usuário
├── app/services/lancamento.py      # sem cobertura nem regra de salário para prestador
├── app/services/limite.py          # usado_no_ciclo usa o ciclo do usuário
├── app/services/resumo.py          # ciclo do usuário + garantir previstos
├── app/services/importacao.py      # prévia e confirmação sem cobertura para prestador
├── app/services/perfil.py          # valida a troca de tipo de renda
├── app/api/routes/ciclos.py        # passa o relógio; /ciclos/atual garante os previstos
├── app/api/routes/recorrencias.py  # passa hoje
└── tests/domain/test_ciclo.py, tests/domain/test_usuario.py, tests/api/test_prestador.py
```

**Structure Decision**: monólito FastAPI em `backend/`, como nas features anteriores. Regra de
ciclo e de troca em `domain/`; `services/ciclo.py` é o único lugar que decide qual regra usar.

## Decisões

Detalhes e alternativas em [research.md](research.md).

- **Ponto único**: `ciclo_da_data_do_usuario(db, usuario_id, data, hoje)` e
  `ciclo_atual_do_usuario(db, usuario_id, hoje)`; `obter_ciclo_*`, limite, resumo, recorrência e
  importação passam a usá-las.
- **`Ciclo.mes_atual`**: campo novo com padrão `False`; `aberto` = `fim is None or mes_atual`.
  Construções existentes de `Ciclo` continuam válidas.
- **Cobertura**: `_problema_depois_da_mudanca` devolve `None` para prestador; isso cobre
  lançamento, dívida (`verificar_novos_lancamentos`) e cartela de uma vez.
- **Salário do prestador**: `_validar_salario` e a validação de data futura da importação só
  valem quando o ciclo é pelo salário; `Lancamento.abre_ciclo` é falso para prestador.
- **Previstos do mês**: `garantir_previstos_do_mes` trava as escritas do usuário, chama
  `gerar_previstos` (já idempotente) para o mês atual e grava; não faz nada para `clt*`.
- **Troca de tipo**: `verificar_troca_tipo_renda` é pura; o service coleta salários realizados,
  menor data dos outros e se há salário previsto ou futuro, sob `travar_escritas`.

## Complexity Tracking

Sem violações.
