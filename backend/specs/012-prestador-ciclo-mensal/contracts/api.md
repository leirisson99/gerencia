# Contrato: Tipo de Renda e Ciclo Mensal do Prestador

Mesmas regras das features anteriores (cookie `sessao`, formato único de erro). Todas as
mudanças são aditivas; para contas `clt` nenhuma resposta muda além do campo novo no `/me`.

## Cadastro e perfil

`TipoRenda = "clt" | "prestador" | "clt_prestador"`

- `POST /api/v1/auth/cadastro`: campo opcional `tipo_renda` (padrão `"clt"`). Valor fora da
  lista → 422 `validacao` com `campos.tipo_renda`.
- `GET /api/v1/me` e `PATCH /api/v1/me`: `UsuarioOut` ganha `tipo_renda`.
- `PATCH /api/v1/me` aceita `{"tipo_renda": "prestador"}`. `null` é recusado (422).
- Erros novos do `PATCH /me`, só na troca de `prestador` para `clt`/`clt_prestador`:
  - 409 `lancamentos_sem_ciclo`: "Lance o salário antes: há lançamentos fora de um ciclo de
    salário."
  - 409 `salario_invalido`: "Como CLT, o salário é sempre realizado e não tem data futura.
    Ajuste os lançamentos em Salário antes de trocar."

## Ciclos (prestador)

`CicloOut` não muda de forma. Para `prestador`:

- `GET /api/v1/ciclos/atual` → mês de hoje, `aberto: true`; nunca 404. Gera os previstos do
  mês das recorrências ativas (idempotente).
- `GET /api/v1/ciclos/{data}` → mês da data; `aberto` só no mês de hoje.

```json
{ "inicio": "2026-10-01", "fim": "2026-10-31", "aberto": true,
  "anterior": "2026-09-01", "proximo": null }
```

- `GET /api/v1/ciclos/{data}/lancamentos` e `/resumo` → lançamentos e resumo do mês. O resumo
  também garante os previstos do mês atual.

## Lançamentos, dívidas, cartelas e importação (prestador)

- Nunca retornam 409 `salario_necessario`, `antes_do_primeiro_ciclo` nem
  `lancamentos_sem_ciclo`.
- Lançamento em "Salário" aceita `status: "previsto"` e data futura; `abre_ciclo` é sempre
  `false`.
- Prévia de importação nunca marca linha como `antes_do_primeiro_ciclo`; confirmação aceita
  "Salário" com data futura.
- `POST /api/v1/recorrencias` gera o previsto no mês atual; "Salário" continua recusado em
  recorrência (422).
