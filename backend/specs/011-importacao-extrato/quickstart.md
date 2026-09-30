# Quickstart: Importação de Extrato

Pré-requisitos e ambiente iguais aos da [002](../002-cadastro-login/quickstart.md). O contrato
está em [contracts/api.md](contracts/api.md) e as regras em [research.md](research.md).

## Migração, testes e lint

```bash
cd backend
uv sync                                   # instala pdfplumber
uv run alembic upgrade head               # 0010: lancamento.id_externo
uv run pytest tests/domain/test_extrato_*.py tests/domain/test_importacao.py tests/api/test_importacao.py
uv run pytest
uv run ruff check . && uv run ruff format --check .
uv run alembic downgrade -1 && uv run alembic upgrade head
```

## Validação com os extratos reais (manual, local)

Os arquivos em `extratos/` não são versionados. Com a API rodando e um usuário logado:

1. `GET /api/v1/importacoes/bancos` lista Itaú, Inter, Mercado Pago, Neon, Nubank e "Outro
   banco".
2. **Contagem cruzada**: a prévia do PDF do Nubank tem o mesmo número de linhas e a mesma soma
   de valores que a do OFX do Nubank. O mesmo vale para o Inter (PDF, OFX e CSV).
3. **Itaú, Mercado Pago e Neon (PDF)**: a soma das entradas e das saídas da prévia bate com os
   totais impressos no próprio extrato, e nenhuma linha "SALDO DO DIA" ou "Saldo do dia" aparece.
4. **Histórico**: com um usuário novo, importe o OFX do Inter marcando a linha de crédito do
   salário como "Salário" e o resto nas categorias de saída → 201. `GET /ciclos/atual` começa na
   data do salário.
5. **Reimportação**: envie o mesmo OFX de novo. A prévia vem com tudo em `ja_importada`, e
   confirmar essas linhas devolve `criados: 0`.
6. **Cruzamento de formatos**: envie o CSV do Inter depois do OFX. As linhas vêm como
   `possivel_duplicada`.
7. **Sugestão**: importe o CSV do Nubank depois de categorizar o OFX. As descrições iguais vêm com
   a categoria sugerida.
8. **Frontend**: tela "Importar extrato" com o mesmo fluxo de ponta a ponta.

## Resultado esperado

Todos os passos respondem como descrito, `uv run pytest` passa e o `ruff` não aponta nada.
