# Research: Painel do Administrador

## R1. Criação do administrador

- **Decision**: comando `uv run python -m app.cli criar-admin --nome ... --email ... --telefone
  ... --cargo ...`. Usa as validações do cadastro, grava `papel = admin` e
  `troca_senha_obrigatoria = true`, e imprime a senha temporária uma vez. Não cria categorias.
- **Rationale**: a constituição exige criação só no servidor. Gerar a senha evita que ela fique
  no histórico do shell ou em variável de ambiente.
- **Alternatives considered**: variáveis `ADMIN_EMAIL/ADMIN_SENHA` no deploy (senha em texto no
  ambiente); promover um usuário existente (mistura conta financeira com administração).

## R2. Um único administrador

- **Decision**: índice único parcial `uq_usuario_admin_unico ON usuario (papel) WHERE papel =
  'admin'`, além da checagem no serviço.
- **Rationale**: garante a regra no banco mesmo com dois comandos simultâneos. Remover o índice
  numa migração futura libera vários administradores.

## R3. Senha temporária

- **Decision**: 12 caracteres de letras e dígitos com `secrets`, com pelo menos uma letra e um
  dígito; validada por `validar_senha`.
- **Rationale**: ~71 bits de entropia, fácil de ditar, sempre aceita pela regra do cadastro.

## R4. Autorização

- **Decision**: dependência `administrador` sobre `autenticacao` (sessão válida, sem troca
  pendente); papel diferente de `admin` → 403 `acesso_negado`.
- **Rationale**: reaproveita a sessão e a troca obrigatória da 002.

## R5. Alvo do reset

- **Decision**: só contas com `papel = usuario`; id inexistente ou do administrador → 404
  `nao_encontrado`. O administrador troca a própria senha por `PUT /me/senha`.

## R6. Auditoria

- **Decision**: tabela `acao_admin (admin_id, acao, usuario_alvo_id, ocorrida_em)`, gravada na
  mesma transação do reset. Sem rota de leitura (P0 não pede); consulta direta no banco.
- **Rationale**: FR-008; a mesma transação garante que não há reset sem registro.

## R7. Listagem

- **Decision**: sem paginação; `busca` opcional com `ILIKE %termo%` em nome ou e-mail; ordem por
  nome e id.
- **Rationale**: dezenas a centenas de contas; paginação é complexidade sem uso atual.
