# Implementation Plan: Contas compartilhadas

**Branch**: `020-conta-compartilhada` | **Date**: 2026-10-16 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/020-conta-compartilhada/spec.md`

## Summary

Quatro tabelas novas (`conta_compartilhada`, `participante_conta`, `cobranca_mensal`,
`cota_cobranca`) e nenhuma coluna nova em `lancamento`, `divida` ou `recorrencia`. O dono
cadastra a conta e convida por e-mail; o convidado aceita e escolhe a própria categoria. A
cobrança do mês é calculada por uma função pura (`ratear`) só entre os participantes que
aceitaram, e cada participante recebe um lançamento previsto **da própria cota, no próprio
usuário**, materializado quando ele mesmo lê o ciclo; o lançamento fica protegido contra
exclusão e alteração de valor ou data. O status da cota ("pendente / informado / confirmado")
é derivado desse lançamento mais a confirmação do dono, então nada escreve no saldo de outro
usuário (mesmo padrão idempotente de `garantir_previstos_do_mes`), nunca por ação de outro
usuário. O acesso a uma conta passa por um único ponto (`conta_visivel`): dono ou participante
`aceito`; qualquer outro recebe 404. A constituição já tem as emendas 8.0.0 (MAJOR) e 8.1.0 (MINOR) que abrem essa
exceção ao isolamento por usuário, com a visibilidade mínima decidida na clarificação (hoje na versão 8.1.0).

## Technical Context

**Language/Version**: Python 3.12 (backend) e TypeScript, Next.js (frontend em `../frontend`)

**Primary Dependencies**: FastAPI, SQLAlchemy 2, Alembic, Pydantic v2; Next.js + shadcn/ui

**Storage**: PostgreSQL 17: 4 tabelas novas (a cota guarda `confirmado_em`, não um status), 1 `CHECK` alterado (`evento_uso`)

**Testing**: pytest com PostgreSQL; domínio em `tests/domain/`, API em `tests/api/`

**Target Platform**: servidor Linux (Easypanel)

**Project Type**: aplicação web (API + frontend)

**Performance Goals**: máx. 20 participantes por conta; materialização dos lançamentos limitada
às cotas do próprio usuário sem lançamento (índice parcial); nenhuma consulta nova nas telas que
não usam o módulo, exceto uma chamada barata ao ler o ciclo (ver research R3)

**Constraints**: zero mudança de comportamento para quem não usa o módulo; soma das cotas == total
sempre; nada visível a quem não é dono nem participante aceito; administrador só vê contagens

**Scale/Scope**: 4 modelos, 1 domínio puro, 1 service, 1 arquivo de rotas (~12 rotas), 1 gancho
na leitura do ciclo, 3 telas no frontend

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.* Constituição 8.1.0.

| Princípio | Verificação | Status |
| --- | --- | --- |
| I. Integridade financeira | Centavos `int`; `ratear` garante soma das cotas == total entre os aceitos; cada pessoa tem lançamento só da própria cota, protegido (409) contra exclusão e alteração de valor ou data; cota de outro nunca entra no saldo; confirmar não escreve em lançamento. | ✅ |
| II. Ciclo derivado | Nenhuma coluna de ciclo; lançamento previsto cai no ciclo existente do próprio participante (carteira PF); sem ciclo aberto/coberto, a cota espera sem lançamento. | ✅ |
| III. Domínio puro e teste primeiro | `domain/conta_compartilhada.py` (`ratear`, `validar_divisao`, `status_do_convite`) testado antes de qualquer service. | ✅ |
| IV. Contratos tipados | Schemas Pydantic próprios; `Literal` para modo e status; erros no formato único. | ✅ |
| V. Isolamento | Exceção prevista na 8.1.0: acesso por `conta_visivel` (dono ou participante aceito), 404 para o resto; convidado vê só nome do dono, título e data; participantes veem nome e status dos demais; sem e-mail nem valor alheio. | ✅ (emenda 8.1.0) |
| VI. Escopo | Módulo P1 pedido explicitamente; previsto na 8.1.0; só carteira PF; sem pagamento real, sem push de convite, sem consolidado. | ✅ (emenda 8.1.0) |

**Re-check pós-design**: com a emenda 8.1.0 já escrita, sem outras violações. Complexity
Tracking abaixo registra as exceções que ela autoriza.

## Project Structure

### Documentation (this feature)

```text
specs/020-conta-compartilhada/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/contas-compartilhadas.md
└── tasks.md             # /speckit-tasks
```

### Source Code

```text
backend/
├── alembic/versions/0019_conta_compartilhada.py        # novo (+ CHECK de evento_uso)
├── app/
│   ├── domain/conta_compartilhada.py                   # novo: ratear, validar_divisao, convite_expirado
│   ├── models/conta_compartilhada.py                   # novo: 4 modelos
│   ├── models/__init__.py                              # importa os modelos novos
│   ├── models/evento_uso.py                            # + 5 tipos
│   ├── schemas/conta_compartilhada.py                  # novo
│   ├── services/conta_compartilhada.py                 # novo: contas, convites, cobranças, cotas, conta_visivel
│   ├── services/auth.py                                # cadastrar: vincula convites pendentes do e-mail
│   ├── services/lancamento.py                          # recusa excluir e alterar valor/data de lançamento de cota
│   ├── services/ciclo.py                               # gancho: materializar_cotas_do_usuario antes de ler o ciclo
│   ├── services/admin.py                               # contagens do módulo
│   ├── main.py                                         # include_router
│   └── api/routes/contas_compartilhadas.py             # novo
└── tests/
    ├── domain/test_conta_compartilhada.py              # novo
    ├── api/test_contas_compartilhadas.py               # novo
    └── api/test_isolamento.py                          # + casos do módulo

frontend/
├── lib/api/contas-compartilhadas.ts, lib/api/types.ts
├── app/(app)/contas-compartilhadas/page.tsx, [id]/page.tsx
├── features/contas-compartilhadas/*                    # cartão, dialog de conta, convites, cobrança
└── components/layout/{app-sidebar,barra-inferior}.tsx  # item no menu
```

**Structure Decision**: aplicação web existente (backend + frontend). O módulo segue as camadas
atuais: regra em `domain/`, orquestração em `services/`, rotas finas.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| Exceção ao princípio V (dado compartilhado entre usuários) | A feature existe para dividir uma conta entre usuários do app, com total e nº de pessoas visíveis a todos. | Participantes em texto livre foi rejeitado pelo usuário; copiar a conta para cada usuário duplicaria o total e perderia o vínculo. |
| Nome de um usuário visível a outros participantes (dado pessoal do cadastro) | A clarificação pediu nome e status dos demais. | Mostrar só a posição ("pessoa 3") foi descartado na clarificação. |
| Item P1 (princípio VI) | Pedido explícito do usuário. | Não implementar. |
| Escrita em `lancamento` por regra do módulo (bloqueio de exclusão e de valor/data) | Garante que a cota continue batendo com o que os outros participantes esperam. | Deixar livre faria o saldo divergir da conta. |
