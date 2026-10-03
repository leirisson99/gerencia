# Contrato: carteiras PF e PJ (019)

Todas as mudanças são aditivas. Um cliente que não envia `carteira` continua vendo e gravando
só a PF.

## Erros novos (formato `ErroOut`)

| Status | Código | Quando |
| --- | --- | --- |
| 409 | `carteira_pj_desligada` | Ler ou gravar `carteira=pj` sem a PJ ligada |
| 409 | `tipo_sem_pj` | Ligar a PJ sendo `clt` |
| 409 | `pj_com_dados` | Desligar a PJ ou trocar para `clt` com dados PJ |
| 409 | `categoria_conflitante` | Ligar a PJ com categoria de mesmo nome e tipo diferente |
| 409 | `lancamento_de_retirada` | Editar ou excluir um lado da retirada pelo lançamento |
| 422 | `validacao` (`campos.categoria_id`) | "Salário" na PJ |
| 422 | `validacao` (`campos.valor` / `campos.data`) | Retirada com valor ≤ 0 ou data futura |
| 409 | `salario_necessario` / `antes_do_primeiro_ciclo` | Lado PF da retirada fora de ciclo de salário (mesmos códigos do lançamento PF) |

## Perfil

- `GET /api/v1/me` → `UsuarioOut` ganha `tem_pj: bool`.
- `PATCH /api/v1/me` aceita `tem_pj: bool`. Ligar cria as categorias de sistema da PJ.

## Ciclos (leitura)

`GET /api/v1/ciclos/atual`, `/ciclos/{data}`, `/ciclos/{data}/lancamentos` e
`/ciclos/{data}/resumo` aceitam `?carteira=pf|pj` (padrão `pf`).

- `pj`: o ciclo é o mês do calendário que contém a data, e `anterior` existe se houver
  lançamento PJ antes do mês. Na PJ nunca há `404 sem_ciclo`.
- Lista e resumo trazem só lançamentos da carteira.
- Abrir a PJ do mês atual gera, de forma idempotente, os previstos das recorrências PJ.

## Lançamentos

- `POST /api/v1/lancamentos`: `carteira?: "pf" | "pj"` (padrão `pf`).
- `PATCH /api/v1/lancamentos/{id}`: `carteira?` (muda de carteira seguindo as regras da
  carteira de destino; lado de retirada → 409).
- `LancamentoOut` ganha `carteira` e `retirada_id` (lado de retirada, ou `null`).

## Recorrências

- `POST /api/v1/recorrencias`: `carteira?` (padrão `pf`). Não muda depois de criada.
- `GET /api/v1/recorrencias?carteira=pf|pj` (sem o parâmetro: todas).
- `RecorrenciaOut` ganha `carteira`.

## Retiradas (novas)

| Método | Rota | Corpo | Resposta |
| --- | --- | --- | --- |
| POST | `/api/v1/retiradas` | `{ "valor": 500000, "data": "2026-10-25", "descricao"?: str }` | 201 `RetiradaOut` |
| GET | `/api/v1/retiradas` | — | `RetiradaOut[]`, da data mais recente para a mais antiga |
| GET | `/api/v1/retiradas/{id}` | — | `RetiradaOut`; 404 se não existir ou for de outro usuário |
| PATCH | `/api/v1/retiradas/{id}` | `{ "valor"?, "data"?, "descricao"? }` | `RetiradaOut` |
| DELETE | `/api/v1/retiradas/{id}` | — | 204 |

```json
{
  "id": 3,
  "data": "2026-10-25",
  "valor": 500000,
  "descricao": null,
  "lancamento_pj_id": 41,
  "lancamento_pf_id": 42
}
```

A `descricao` vai para os dois lados. Toda rota exige a PJ ligada (409
`carteira_pj_desligada`).

## Lembretes

`GET /api/v1/lembretes`: cada item ganha `carteira: "pf" | "pj"` (lembrete livre = `pf`).

## Administrador

- `ContagensContaOut` ganha `retiradas: int`.
- `TipoEvento` ganha `retirada_feita`, `retirada_editada` e `retirada_excluida`.
