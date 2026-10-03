# Implementation Plan: Carteiras PF e PJ

**Branch**: `019-carteira-pj` | **Date**: 2026-10-03 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/019-carteira-pj/spec.md`

## Summary

`lancamento` e `recorrencia` ganham a coluna `carteira` (`pf` por padrão), `usuario` ganha
`tem_pj`, e uma tabela nova `retirada` é dona dos dois lançamentos (saída PJ e entrada PF). O
ciclo continua decidido num único ponto: `ciclo_pelo_mes(tipo_renda, carteira)` diz que a PJ é
sempre o mês do calendário. Todas as consultas de ciclo, saldo, limite e cobertura por salário
passam a filtrar pela carteira, com padrão `pf`, e por isso o comportamento atual não muda. As
rotas de ciclo aceitam `?carteira=`, há CRUD de `/retiradas`, e o frontend ganha o seletor
PF | PJ (cookie), a carteira nos formulários, o botão "Retirar para PF" e o interruptor no
perfil.

## Technical Context

**Language/Version**: Python 3.12 (backend) e TypeScript, Next.js (frontend em `../frontend`)

**Primary Dependencies**: FastAPI, SQLAlchemy 2, Alembic, Pydantic v2; Next.js + shadcn/ui

**Storage**: PostgreSQL 17: 3 colunas novas, 1 tabela nova, 1 índice trocado, 1 `CHECK`
alterado

**Testing**: pytest com PostgreSQL; domínio em `tests/domain/`, API em `tests/api/`

**Target Platform**: servidor Linux (Easypanel)

**Project Type**: aplicação web (API + frontend)

**Performance Goals**: as consultas de ciclo usam o índice `(usuario_id, carteira, data)`;
nenhuma consulta nova por requisição além do filtro

**Constraints**: zero mudança de comportamento para quem não liga a PJ (SC-004); retirada
sempre consistente (SC-002); nenhuma leitura mistura carteiras (SC-003)

**Scale/Scope**: cerca de 11 arquivos de service tocados, 5 rotas novas, 4 rotas com parâmetro
novo e 6 a 8 telas do frontend lendo a carteira

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.* Constituição 7.0.0.

| Princípio | Verificação | Status |
| --- | --- | --- |
| I. Integridade financeira | Centavos `int`; saldo e gasto sempre de uma carteira; retirada com dois lados numa transação, presos à retirada; sem `conta_no_saldo = False` artificial. | ✅ |
| II. Ciclo derivado | Nenhuma coluna de ciclo; `ciclo_pelo_mes(tipo, carteira)` é o único ponto; a PJ usa `ciclo_mensal`; a cobertura por salário filtra a PF; "Salário" recusado na PJ. | ✅ |
| III. Domínio puro e teste primeiro | `domain/usuario` (carteira, `pode_ter_pj`, `verificar_pj`) e `domain/retirada` testados antes; testes de API por rota de leitura garantindo o isolamento entre carteiras. | ✅ |
| IV. Contratos tipados | `Carteira = Literal["pf", "pj"]`; schemas aditivos; erros no formato único. | ✅ |
| V. Isolamento | Retirada filtrada por usuário, 404 para a de outro usuário (com teste); o admin vê só a contagem e os eventos. | ✅ |
| VI. Escopo | Fase 1 exatamente como a emenda: dívidas, cartelas, serviços e importação só na PF; sem cálculo de imposto; sem consolidado. Campo `carteira` opcional (regra 7). | ✅ |

**Re-check pós-design**: sem violações. Complexity Tracking vazio.

## Project Structure

### Documentation (this feature)

```text
specs/019-carteira-pj/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/carteiras.md
├── checklists/requirements.md
└── tasks.md             # /speckit-tasks
```

### Source Code

```text
backend/
├── alembic/versions/0018_carteira_pj.py               # novo
├── app/
│   ├── domain/usuario.py                              # ciclo_pelo_mes(tipo, carteira), pode_ter_pj, verificar_pj
│   ├── domain/retirada.py                             # novo: validar_retirada, lados_da_retirada
│   ├── domain/categoria.py                            # nomes das 2 categorias de sistema da PJ
│   ├── models/{lancamento,recorrencia,usuario}.py     # + carteira / tem_pj
│   ├── models/retirada.py                             # novo
│   ├── models/evento_uso.py                           # + 3 tipos
│   ├── schemas/{lancamento,recorrencia,usuario,lembrete,admin}.py  # + carteira, tem_pj, retiradas
│   ├── schemas/retirada.py                            # novo
│   ├── services/ciclo.py                              # carteira em ciclo, lançamentos, primeira data, salários
│   ├── services/lancamento.py                         # carteira na criação/edição, Salário na PJ, lado de retirada preso
│   ├── services/recorrencia.py                        # carteira; gerar_previstos e garantir_previstos_do_mes por carteira
│   ├── services/{resumo,limite}.py                    # carteira nas consultas
│   ├── services/{importacao,perfil}.py                # cobertura só PF; tem_pj e troca de tipo
│   ├── services/categoria.py                          # garantir_categorias_pj
│   ├── services/lembrete.py                           # carteira nos itens
│   ├── services/retirada.py                           # novo: criar, listar, obter, editar, excluir
│   ├── services/admin.py                              # contagem de retiradas
│   └── api/routes/{ciclos,recorrencias,retiradas}.py  # ?carteira=, rotas novas
└── tests/
    ├── domain/test_carteira.py                        # novo
    ├── domain/test_retirada.py                        # novo
    ├── api/test_carteira_pj.py                        # novo: perfil, ciclo PJ, isolamento entre carteiras, cobertura
    └── api/test_retiradas.py                          # novo

frontend/
├── lib/carteira.ts                                    # novo: leitura do cookie no servidor
├── components/layout/seletor-carteira.tsx             # novo, no app-shell
├── lib/api/{server,types}.ts, lib/api/retiradas.ts    # carteira nas chamadas; API de retirada
├── features/lancamentos/*, features/recorrencias/*    # carteira no formulário
├── features/retiradas/dialog-retirada.tsx             # novo: "Retirar para PF"
├── features/perfil/form-perfil.tsx                    # interruptor "Tenho CNPJ"
└── features/lembretes/*                               # marca PF/PJ
```

**Structure Decision**: as camadas de sempre. A regra de qual ciclo vale fica só em
`domain/usuario.ciclo_pelo_mes`; os services recebem `carteira` com padrão `"pf"`, então cada
chamador existente segue correto sem mudança.

## Ordem de implementação

1. Domínio e testes (`ciclo_pelo_mes` com carteira, `pode_ter_pj`, `verificar_pj`,
   retirada).
2. Migração `0018`, modelos e schemas.
3. US1: perfil `tem_pj` e categorias de sistema; `carteira` nos services de ciclo, lançamento,
   resumo e limite; cobertura só PF; "Salário" recusado na PJ; testes de isolamento por rota.
4. US2: `services/retirada.py`, rotas e lados presos em `lancamento`.
5. US3: recorrências por carteira.
6. US4 e US5: lembretes com a carteira; desligar a PJ e troca de tipo.
7. Admin: eventos e contagem de retiradas.
8. Frontend: seletor, formulários, retirada, perfil, lembretes.
9. CLAUDE.md (glossário: Carteira, Retirada; modelo de dados; regras de cálculo), suíte
   completa, lint, build e quickstart.

## Riscos

- **Esquecer o filtro de carteira numa consulta** faz um lançamento PJ vazar para a PF (ou o
  contrário). Mitigação: um teste por rota de leitura com um lançamento em cada carteira, e uma
  busca no código por `select(Lancamento)` revisada na tarefa de acabamento.
- **Cobertura por salário** contando lançamentos PJ bloquearia a PJ do `clt_prestador`.
  Mitigação: teste explícito sem salário (US1-4) e na troca de tipo.

## Complexity Tracking

Nenhuma violação a justificar.
