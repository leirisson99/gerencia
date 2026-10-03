# Quickstart: validar as carteiras PF e PJ (019)

## Pré-requisitos

Rode tudo dentro de `backend/`, com o Docker Desktop aberto:

```bash
docker compose up -d db
uv sync
uv run alembic upgrade head        # 0018: carteira, tem_pj e retirada
uv run uvicorn app.main:app --reload
```

O frontend fica em `../frontend` (`npm run dev`).

## Testes automatizados

```bash
uv run pytest tests/domain/test_carteira.py tests/domain/test_retirada.py
uv run pytest tests/api/test_carteira_pj.py tests/api/test_retiradas.py
uv run pytest                       # a suíte existente continua verde (SC-004)
uv run ruff check . && uv run ruff format --check .
```

## Cenários de ponta a ponta: o Carlos (exemplo de referência)

1. **Ligar a PJ.** Cadastre o Carlos como `prestador` e ligue "Tenho CNPJ" no perfil. O
   seletor PF | PJ aparece no topo.
2. **Lançar na PJ.** Na PJ de outubro, lance + R$ 8.000 (Renda extra), − R$ 75 (crie
   "Impostos") e − R$ 300 (crie "Contador"). O saldo PJ fica em R$ 7.625, e a PF continua
   zerada.
3. **Retirar.** Use "Retirar para PF": R$ 5.000 em 25/10. O saldo PJ vai a R$ 2.625. Na PF
   aparece + R$ 5.000 em "Pró-labore e lucros".
4. **Gastar na PF.** Lance − R$ 1.800 (Moradia) e − R$ 900 (Alimentação) na PF. O saldo PF fica
   em R$ 2.300 (SC-001).
5. **Lados presos.** Tente editar ou excluir o lançamento "Retirada para PF" pela lista: deve
   ser recusado com a orientação de alterar pela retirada. Edite a retirada para R$ 4.500: os
   dois lados mudam.
6. **Recorrência PJ.** Crie "DAS" R$ 75, dia 20, na PJ. Abra a PJ de outubro duas vezes: há um
   único previsto em 20/10, e nada na PF.
7. **Lembretes.** Com o DAS previsto para amanhã, os lembretes mostram o item marcado PJ.

## Cenários da Ana (`clt_prestador`)

8. Ligue a PJ sem lançar salário. Lançar na PJ funciona; lançar na PF pede o salário primeiro.
9. Tente lançar "Salário" na PJ: recusado.
10. Com dados PJ, tente trocar para `clt` ou desligar a PJ: recusado com explicação.

## Sem PJ

11. Uma conta `clt` comum não vê o seletor e não percebe nenhuma diferença.
