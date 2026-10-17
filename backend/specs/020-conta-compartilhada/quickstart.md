# Quickstart: validar contas compartilhadas

Pré-requisitos: `docker compose up -d db`, `uv sync`, `uv run alembic upgrade head`.

## Automático

```bash
cd backend
uv run pytest tests/domain/test_conta_compartilhada.py tests/api/test_contas_compartilhadas.py \
  tests/api/test_isolamento.py
uv run pytest            # regressão completa
uv run ruff check . && uv run ruff format --check .
uv run alembic downgrade -1 && uv run alembic upgrade head
```

## Manual (dois navegadores/perfis)

1. Ana (dono) cria "Energia", dia 10, modo igual, convida 5 e-mails (um sem conta).
2. Bia aceita e escolhe a categoria; confira: total, nº de pessoas e minha cota; dos outros só
   nome e status.
3. Ana gera a cobrança de outubro com R$ 600,00: cotas de R$ 100,00 cada.
4. Bia abre o ciclo: aparece um previsto de R$ 100,00; o saldo não muda até realizar. Com
   só 3 dos 6 convidados aceitos, a divisão é entre os 3 (cota de R$ 200,00).
5. Bia realiza o lançamento ("paguei"): a cota vira "informado". Ana confirma. Bia cancela
   (volta para previsto): a cota volta a "pendente". Bia tenta excluir ou mudar o valor do
   lançamento: 409.
6. Conta de água sem valor fixo: Ana vê "falta informar o total de outubro" até informar.
   Um terceiro usuário abre a conta pelo id: 404. Água ÷ 3 com R$ 100,00: 33,33 / 33,33 / 33,34.
7. Remova um participante: a cobrança do mês continua igual; a próxima já o ignora.
