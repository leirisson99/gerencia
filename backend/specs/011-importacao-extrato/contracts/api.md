# Contrato da API: Importação de Extrato

Base `/api/v1`, corpo JSON, cookie `sessao`, formato único de erro (como na 002). Todas as rotas
exigem sessão sem troca de senha pendente. Valores em centavos inteiros; datas `YYYY-MM-DD`.

## Novos códigos de erro

| Código | HTTP | Quando |
| --- | --- | --- |
| `extrato_invalido` | 422 | arquivo ilegível no formato escolhido, base64 inválido ou layout de PDF não reconhecido. A mensagem sugere OFX ou CSV |
| `pdf_sem_texto` | 422 | PDF sem texto (escaneado) |
| `extrato_grande` | 413 | arquivo acima de 2 MB ou com mais de 5.000 linhas |
| `formato_indisponivel` | 422 | banco não oferece o formato escolhido (`campos.formato`) |
| `validacao` | 422 | inclui erros por linha na confirmação: `campos["linhas.3.categoria_id"]` |
| `salario_necessario` / `antes_do_primeiro_ciclo` | 409 | cobertura do lote, como no lançamento manual |
| `conflito_importacao` | 409 | outra confirmação gravou as mesmas linhas ao mesmo tempo |
| `nao_encontrado` | 404 | categoria inexistente ou de outro usuário numa linha |

## `GET /importacoes/bancos` → 200 `BancoOut[]`

```json
[
  { "codigo": "itau", "nome": "Itaú", "formatos": ["ofx", "pdf"] },
  { "codigo": "nubank", "nome": "Nubank", "formatos": ["ofx", "csv", "pdf"] },
  { "codigo": "outro", "nome": "Outro banco", "formatos": ["ofx", "csv_generico"] }
]
```

Ordem: bancos por nome, "Outro banco" por último.

## `POST /importacoes/previa` → 200 `PreviaOut`

**PreviaIn**

```json
{
  "banco": "inter",
  "formato": "csv",
  "arquivo_base64": "RGF0YSBMYW7Dp2FtZW50bzsuLi4=",
  "mapeamento": null
}
```

`mapeamento` é obrigatório só em `csv_generico`, e é recusado nos demais formatos:

```json
{
  "separador": ";",
  "pular_linhas": 0,
  "tem_cabecalho": true,
  "coluna_data": 0,
  "formato_data": "dd/mm/aaaa",
  "coluna_descricao": 1,
  "coluna_valor": 2,
  "coluna_credito": null,
  "coluna_debito": null,
  "separador_decimal": ","
}
```

- As colunas são índices a partir de 0.
- Envie `coluna_valor` **ou** o par `coluna_credito` e `coluna_debito`.
- `separador` aceita `;`, `,` e `\t`.
- `formato_data` aceita `dd/mm/aaaa`, `dd-mm-aaaa`, `aaaa-mm-dd` e `mm/dd/aaaa`.
- `separador_decimal` aceita `,` e `.`.

**PreviaOut**

```json
{
  "linhas": [
    {
      "id_externo": "inter:csv:h:4f1c…",
      "data": "2026-09-02",
      "valor": 4590,
      "tipo": "saida",
      "descricao": "Pix enviado: Padaria Central",
      "categoria_sugerida_id": 12,
      "situacao": "nova"
    }
  ],
  "resumo": { "nova": 10, "ja_importada": 2, "possivel_duplicada": 1,
              "antes_do_primeiro_ciclo": 0, "invalida": 0 }
}
```

Nada é gravado. Linhas em ordem de data e, no mesmo dia, na ordem do arquivo.

## `POST /importacoes` → 201 `ImportacaoOut`

**ImportacaoIn**

```json
{
  "linhas": [
    {
      "id_externo": "inter:csv:h:4f1c…",
      "data": "2026-09-02",
      "valor": 4590,
      "tipo": "saida",
      "descricao": "Pix enviado: Padaria Central",
      "categoria_id": 12
    }
  ]
}
```

- Regras dos campos: `valor` `StrictInt` > 0 e ≤ 99.999.999.999; `id_externo` com 1 a 120
  caracteres; `descricao` com no máximo 200 caracteres (cortada no limite na prévia).
- Entre 1 e 5.000 linhas; campos extras são recusados.

**ImportacaoOut**

```json
{ "criados": 9, "ignoradas": 1, "lancamento_ids": [101, 102] }
```

`ignoradas` conta as linhas cujo `id_externo` já existia ou se repetia no lote. Tudo ou nada: qualquer
erro de linha ou de cobertura recusa o lote inteiro.

## Mudança em `LancamentoOut`

Campo novo `importado: bool`. A mudança é aditiva, então vale para todas as respostas de
lançamento.
