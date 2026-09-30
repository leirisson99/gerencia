# Data Model: Importação de Extrato

Migração reversível `0010_importacao` (a feature 010 não tem migração). Valores em centavos
(`BIGINT`), datas `date`.

## lancamento (coluna nova)

| Campo | Tipo | Regras |
| --- | --- | --- |
| id_externo | varchar(120), null | Preenchido só em lançamentos importados. Formato em [research.md](research.md) R7 |

**Índice**: `uq_lancamento_usuario_id_externo` único em `(usuario_id, id_externo)` `WHERE
id_externo IS NOT NULL`.

`downgrade`: remove o índice e a coluna. Lançamentos importados continuam existindo como
lançamentos comuns.

Nenhuma tabela nova: a prévia não é guardada.

## Estruturas de domínio (não guardadas)

```text
LinhaExtrato(data: date, valor: int, descricao: str, id_origem: str | None)
    # valor com sinal, em centavos: > 0 entrada, < 0 saída
LinhaPdf(pagina: int, topo: float, texto: str)
Banco(codigo: str, nome: str, leitores: dict[Formato, Leitor])
    # Formato = "ofx" | "csv" | "pdf" | "csv_generico"
MapeamentoCsv(separador, pular_linhas, tem_cabecalho, coluna_data, formato_data,
              coluna_descricao, coluna_valor | (coluna_credito, coluna_debito),
              separador_decimal)
LinhaPrevia(id_externo, data, valor: int > 0, tipo, descricao, categoria_sugerida_id, situacao)
    # situacao = "nova" | "ja_importada" | "possivel_duplicada"
    #          | "antes_do_primeiro_ciclo" | "invalida"
```

## Regras

- `valor` na prévia e na confirmação é sempre positivo; o sinal do extrato vira `tipo`
  (`entrada` > 0, `saida` < 0).
- Linha confirmada vira `Lancamento(status="realizado", conta_no_saldo=True, tipo=categoria.tipo,
  id_externo=…)`. O `tipo` da linha precisa ser igual ao da categoria.
- Lançamento importado é editável e excluível como qualquer outro (FR-016); editar não muda o
  `id_externo`, e excluir libera o id para uma nova importação.
