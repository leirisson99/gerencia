from collections import Counter
from datetime import date

from app.domain.ciclo import Ciclo, ProblemaCobertura
from app.domain.extrato import LinhaExtrato
from app.domain.importacao import (
    classificar,
    cobertura_do_lote,
    ids_externos,
    normalizar_descricao,
    novo_ciclo_aberto,
    sugerir_categoria,
    tipo_da_linha,
)

D1, D2, D3 = date(2026, 9, 5), date(2026, 9, 6), date(2026, 9, 7)


def test_normalizar_descricao() -> None:
    assert normalizar_descricao("  Uber   TRIP ") == "uber trip"
    assert normalizar_descricao("Café Açaí.") == "cafe acai"
    assert normalizar_descricao("PIX - Padaria São João -") == "pix - padaria sao joao"
    assert normalizar_descricao("") == ""


def test_tipo_da_linha() -> None:
    assert tipo_da_linha(100) == "entrada"
    assert tipo_da_linha(-100) == "saida"


def test_id_externo_usa_id_do_banco_e_formato() -> None:
    linhas = [LinhaExtrato(D1, -800, "Café", "abc-1")]
    assert ids_externos("nubank", "ofx", linhas) == ["nubank:ofx:abc-1"]


def test_id_externo_sem_id_e_estavel_e_separa_linhas_identicas() -> None:
    cafe = LinhaExtrato(D1, -800, "Café")
    linhas = [cafe, LinhaExtrato(D1, -800, "café "), LinhaExtrato(D2, -800, "Café")]
    ids = ids_externos("itau", "pdf", linhas)

    assert len(set(ids)) == 3  # dois cafés iguais no mesmo dia são movimentações diferentes
    assert all(i.startswith("itau:pdf:h:") and len(i) <= 120 for i in ids)
    # Reimportar o mesmo arquivo gera os mesmos ids; o 1º café do dia continua sendo o 1º.
    assert ids_externos("itau", "pdf", linhas) == ids
    assert ids_externos("itau", "pdf", [cafe]) == ids[:1]
    # Outro banco ou formato nunca colide.
    assert ids_externos("inter", "pdf", [cafe])[0] != ids[0]


def test_id_do_banco_repetido_no_arquivo_nao_colide() -> None:
    linhas = [LinhaExtrato(D1, 100, "Estorno", "x"), LinhaExtrato(D1, -100, "Compra", "x")]
    ids = ids_externos("nubank", "csv", linhas)
    assert len(set(ids)) == 2
    assert ids[0] == "nubank:csv:x"


def test_id_do_banco_muito_longo_vira_hash() -> None:
    [id_externo] = ids_externos("outro", "ofx", [LinhaExtrato(D1, 100, "X", "9" * 200)])
    assert len(id_externo) <= 120


def _classificar(
    linhas: list[LinhaExtrato],
    ja_importados: set[str] | None = None,
    existentes: Counter[tuple[date, str, int]] | None = None,
    primeiro_salario: date | None = None,
) -> list[str]:
    ids = [f"id{i}" for i in range(len(linhas))]
    return classificar(
        linhas, ids, ja_importados or set(), existentes or Counter(), primeiro_salario
    )


def test_classificar_linha_nova() -> None:
    assert _classificar([LinhaExtrato(D1, -800, "Café")]) == ["nova"]


def test_classificar_valor_zero_e_invalida() -> None:
    assert _classificar([LinhaExtrato(D1, 0, "Nada")], ja_importados={"id0"}) == ["invalida"]


def test_classificar_ja_importada_vence_as_demais() -> None:
    assert _classificar(
        [LinhaExtrato(D1, -800, "Café")],
        ja_importados={"id0"},
        existentes=Counter({(D1, "saida", 800): 1}),
        primeiro_salario=D3,
    ) == ["ja_importada"]


def test_classificar_antes_do_primeiro_ciclo_so_com_salario_no_sistema() -> None:
    linha = [LinhaExtrato(D1, -800, "Café")]
    assert _classificar(linha, primeiro_salario=D2) == ["antes_do_primeiro_ciclo"]
    assert _classificar(linha, primeiro_salario=D1) == ["nova"]
    assert _classificar(linha, primeiro_salario=None) == ["nova"]  # o lote pode trazer o salário


def test_classificar_possivel_duplicada_consome_os_existentes() -> None:
    cafes = [LinhaExtrato(D1, -800, "Café"), LinhaExtrato(D1, -800, "Café")]
    existentes = Counter({(D1, "saida", 800): 1})
    assert _classificar(cafes, existentes=existentes) == ["possivel_duplicada", "nova"]
    assert existentes == Counter({(D1, "saida", 800): 1})  # não altera o contador recebido


def test_classificar_duplicada_compara_tipo() -> None:
    assert _classificar(
        [LinhaExtrato(D1, 800, "Estorno")], existentes=Counter({(D1, "saida", 800): 1})
    ) == ["nova"]


def test_sugerir_categoria() -> None:
    historico = {"uber trip": (5, "saida"), "salario empresa": (1, "entrada")}
    assert sugerir_categoria("Uber   Trip", "saida", historico) == 5
    assert sugerir_categoria("UBER TRIP", "entrada", historico) is None  # tipo diferente
    assert sugerir_categoria("Padaria", "saida", historico) is None
    assert sugerir_categoria("", "saida", {"": (5, "saida")}) is None


def test_cobertura_do_lote_sem_salario() -> None:
    assert cobertura_do_lote([], None, [(False, D1)]) is ProblemaCobertura.SEM_SALARIO


def test_cobertura_do_lote_com_salario_no_proprio_lote() -> None:
    assert cobertura_do_lote([], None, [(True, D1), (False, D2)]) is None
    assert cobertura_do_lote([], None, [(True, D2), (False, D1)]) is (
        ProblemaCobertura.ANTES_DO_PRIMEIRO_CICLO
    )


def test_cobertura_do_lote_soma_banco_e_lote() -> None:
    assert cobertura_do_lote([D2], None, [(False, D1)]) is ProblemaCobertura.ANTES_DO_PRIMEIRO_CICLO
    assert cobertura_do_lote([D2], D3, [(True, D1), (False, D1)]) is None
    assert cobertura_do_lote([D2], D1, [(False, D3)]) is ProblemaCobertura.ANTES_DO_PRIMEIRO_CICLO


def test_novo_ciclo_aberto_so_quando_o_lote_traz_o_salario_mais_recente() -> None:
    assert novo_ciclo_aberto([D2], [D1]) is None  # salário do passado: ciclo fechado
    assert novo_ciclo_aberto([D2], []) is None
    assert novo_ciclo_aberto([D2], [D2]) is None  # mesma data: o ciclo já existe
    assert novo_ciclo_aberto([D1], [D2, D3]) == Ciclo(D3, None, D2, None)
    assert novo_ciclo_aberto([], [D1]) == Ciclo(D1, None, None, None)
