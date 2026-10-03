# Quickstart: validar a atividade do usuário (018)

## Pré-requisitos

Rode tudo dentro de `backend/`, com o Docker Desktop aberto:

```bash
docker compose up -d db
uv sync
uv run alembic upgrade head        # cria evento_uso e a ação ver_atividade
uv run uvicorn app.main:app --reload
```

O frontend fica em `../frontend` (`npm run dev`), e o admin vem do `.env` (`ADMIN_EMAIL`,
`ADMIN_SENHA_HASH`).

## Testes automatizados

```bash
uv run pytest tests/domain/test_atividade.py tests/api/test_eventos_uso.py tests/api/test_admin_atividade.py
uv run pytest
uv run ruff check . && uv run ruff format --check .
```

## Cenários de ponta a ponta

1. **Gerar uso.** Rode `uv run python -m app.cli popular-demo`. Depois, como Ana, entre no
   sistema, crie e edite um lançamento, importe um extrato de 20 linhas e deposite numa
   cartela.
2. **Detalhe (US1).** Como admin, abra **Contas** e clique na Ana. Confira:
   - sessões abertas ≥ 1;
   - último acesso = hoje;
   - lançamentos importados = 20;
   - importações = 1;
   - depósitos ≥ 1;
   - zero nas funcionalidades que ela não usou.
3. **Linha do tempo (US2).** No topo, em ordem: "Depositou em cartela", "Importou extrato"
   (uma vez só), "Editou lançamento", "Lançou", "Entrou no sistema". Em **Carregar mais**,
   nenhum item se repete.
4. **Falha não conta.** Como Ana, tente um lançamento recusado (por exemplo, com data antes do
   primeiro salário). Recarregue o detalhe: nenhum evento novo.
5. **Privacidade.** Inspecione a resposta de `GET /api/v1/admin/usuarios/{id}` e de
   `/eventos`. Não pode haver valores, descrições, nomes de categorias, clientes ou cartelas,
   telefone, cargo nem data de nascimento.
6. **Auditoria (US3).** Abrir o detalhe cria um `ver_atividade` no histórico. Reabrir dentro
   de 30 minutos não cria outro.
7. **Acesso.** Como Ana, chamar `GET /api/v1/admin/usuarios/{id_da_ana}` responde 403.
   Chamar com um id inexistente ou com o id do admin responde 404.
8. **Aviso (US4).** A tela de cadastro e o perfil mostram o aviso de transparência.
9. **Retenção.** Rode `uv run python -m app.cli limpar-eventos`: imprime `removidos=0` numa
   base nova.
