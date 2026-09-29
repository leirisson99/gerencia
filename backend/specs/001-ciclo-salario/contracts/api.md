# Contrato da API: Ciclo Aberto pelo Salário

Base: `/api/v1`. Mesmas regras da 002: corpo JSON, cookie `sessao`, formato único de erro
([../../002-cadastro-login/contracts/api.md](../../002-cadastro-login/contracts/api.md)).
Todas as rotas abaixo exigem sessão sem troca de senha pendente (401/403 como na 002). O
OpenAPI gerado é o contrato final.

Datas no formato `YYYY-MM-DD`. Valores em centavos, inteiros.

## Novos códigos de erro

| Código | HTTP | Quando |
| --- | --- | --- |
| `salario_necessario` | 409 | lançamento que não é salário sem nenhum salário lançado. Mensagem: "Lance seu salário para abrir o primeiro ciclo." |
| `antes_do_primeiro_ciclo` | 409 | data do lançamento anterior ao primeiro salário. Mensagem cita a data de início do primeiro ciclo |
| `lancamentos_sem_ciclo` | 409 | editar, excluir ou recategorizar um salário deixaria lançamentos sem ciclo |
| `sem_ciclo` | 404 | consulta de ciclo sem salário lançado, ou data anterior ao primeiro salário |
| `validacao` | 422 | inclui: salário com data futura (`campos.data`), salário previsto (`campos.status`), categoria inativa (`campos.categoria_id`), valor não inteiro, ≤ 0 ou acima do limite (`campos.valor`) |
| `nao_encontrado` | 404 | lançamento ou categoria inexistente ou de outro usuário |

## Schemas

**CategoriaOut**

```json
{ "id": 7, "nome": "Salário", "tipo": "entrada", "sistema": true }
```

**LancamentoIn** (criar)

```json
{
  "valor": 500000,
  "categoria_id": 7,
  "data": "2026-10-05",
  "descricao": "Empresa X",
  "status": "realizado"
}
```

Obrigatórios: `valor`, `categoria_id`, `data`. Opcionais: `descricao` (≤ 200), `status`
(default `realizado`). `tipo` não é aceito (vem da categoria). Campos extras são recusados.

**LancamentoPatch** (editar): os mesmos campos, todos opcionais; só os enviados mudam;
`descricao: null` remove a descrição. `valor`, `categoria_id`, `data` e `status` não aceitam
`null`.

**LancamentoOut**

```json
{
  "id": 42,
  "valor": 500000,
  "tipo": "entrada",
  "categoria_id": 7,
  "data": "2026-10-05",
  "descricao": "Empresa X",
  "status": "realizado",
  "conta_no_saldo": true,
  "abre_ciclo": true,
  "criado_em": "2026-10-05T12:00:00Z"
}
```

`abre_ciclo` é derivado (categoria "Salário" e `realizado`).

**CicloOut**

```json
{
  "inicio": "2026-11-06",
  "fim": "2026-12-04",
  "aberto": false,
  "anterior": "2026-10-05",
  "proximo": "2026-12-05"
}
```

`fim` é `null` no ciclo aberto. `anterior` e `proximo` são as datas de início dos ciclos
vizinhos, ou `null` quando não existem (US3.3); servem para pedir o vizinho em
`GET /ciclos/{data}`.

## Rotas

### `GET /categorias` → 200 `CategoriaOut[]`

Categorias ativas do usuário, ordenadas: "Salário" primeiro, depois entradas e saídas por
nome.

### `POST /lancamentos` → 201 `LancamentoOut`

Erros: 422 `validacao`; 404 `nao_encontrado` (categoria); 409 `salario_necessario`;
409 `antes_do_primeiro_ciclo`.

### `GET /lancamentos/{id}` → 200 `LancamentoOut`

404 se não existe ou é de outro usuário.

### `PATCH /lancamentos/{id}` → 200 `LancamentoOut`

Erros: os de criar, mais 409 `lancamentos_sem_ciclo` quando a mudança afeta um salário; 404.

### `DELETE /lancamentos/{id}` → 204

Erros: 409 `lancamentos_sem_ciclo` (excluir o salário deixaria outros sem ciclo); 404.

### `GET /ciclos/atual` → 200 `CicloOut`

O ciclo mais recente (sempre o aberto). 404 `sem_ciclo` sem salário lançado.

### `GET /ciclos/{data}` → 200 `CicloOut`

O ciclo que contém a data (FR-009). 404 `sem_ciclo` se não há salário ou a data é anterior
ao primeiro. Data inválida → 422.

### `GET /ciclos/{data}/lancamentos` → 200 `LancamentoOut[]`

Lançamentos do ciclo que contém a data, ordenados por `data` e `id`. 404 `sem_ciclo` como
acima.

### `GET /salarios/sugestao` → 200

```json
{ "valor": 500000 }
```

Valor do salário mais recente, ou `null` se não houver (FR-012).
