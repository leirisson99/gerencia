# Contrato: Serviços a Receber

Mesmas regras das features anteriores (cookie `sessao`, formato único de erro). Valores em
centavos, inteiros. Mudanças em rotas existentes são aditivas.

## Acesso

Todas as rotas de `/api/v1/servicos` exigem sessão e `tipo_renda` `prestador` ou
`clt_prestador`. Para `clt`: 403 `perfil_sem_servicos` ("Serviços a receber são para quem presta
serviço. Mude o tipo de renda no perfil.").

## Tipos

```json
// ServicoOut
{
  "id": 7,
  "cliente": "Loja da Maria",
  "descricao": "Site institucional",
  "valor": 80000,
  "data_prevista": "2026-10-20",
  "categoria_id": 3,
  "lancamento_id": 41,
  "situacao": "a_receber",        // "a_receber" | "atrasado" | "recebido"
  "data_recebimento": null,       // data do lançamento quando recebido
  "valor_recebido": null,         // valor do lançamento quando recebido
  "criado_em": "2026-10-15T15:00:00Z"
}
```

## Rotas

| Método e caminho | Corpo | Resposta |
| --- | --- | --- |
| `GET /api/v1/servicos?situacao=` | — | `ServicoOut[]`, por `data_prevista`, `id`; `situacao` opcional |
| `POST /api/v1/servicos` | `ServicoIn` | 201 `ServicoOut` |
| `GET /api/v1/servicos/{id}` | — | `ServicoOut` |
| `PATCH /api/v1/servicos/{id}` | `ServicoPatch` | `ServicoOut` |
| `DELETE /api/v1/servicos/{id}` | — | 204 |
| `POST /api/v1/servicos/{id}/recebimento` | `RecebimentoIn` | `ServicoOut` |
| `DELETE /api/v1/servicos/{id}/recebimento` | — | `ServicoOut` |

- `ServicoIn`: `cliente` (obrigatório, ≤ 120), `descricao` (opcional, ≤ 200), `valor` (int > 0),
  `data_prevista` (date), `categoria_id` (int).
- `ServicoPatch`: os mesmos campos, todos opcionais; `null` só é aceito em `descricao` (remove).
- `RecebimentoIn`: `data` (date, obrigatório), `valor` (int > 0, opcional).

## Erros

- 404 `nao_encontrado`: serviço inexistente ou de outro usuário; categoria de outro usuário.
- 409 `servico_recebido`: editar, excluir ou receber um serviço já recebido.
- 409 `servico_nao_recebido`: desfazer um recebimento que não existe.
- 409 `salario_necessario` / `antes_do_primeiro_ciclo`: `clt_prestador` sem cobertura de ciclo.
- 422 `validacao`: campos inválidos; `campos.categoria_id` para categoria inativa, de saída ou
  "Salário"; `campos.data` para recebimento com data futura.

## Mudanças em rotas existentes

- `LancamentoOut` ganha `servico_id` (`null` se não for de serviço).
- `PATCH /api/v1/lancamentos/{id}` de lançamento de serviço: 422 `validacao` em `valor`,
  `status`, `categoria_id` ou `data` ("Altere pelo serviço."); descrição continua editável.
- `DELETE /api/v1/lancamentos/{id}` de lançamento de serviço: 409 `lancamento_de_servico`.
- As duas travas só valem enquanto o dono tem acesso a serviços.
- `PATCH /api/v1/me` para `clt` com serviço não recebido: 409 `servicos_pendentes`.
