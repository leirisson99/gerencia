from app.domain.saldo import Movimento, Resumo, resumir

SALARIO, EXTRA, ALIMENTACAO, MORADIA = 1, 2, 3, 4


def entrada(
    categoria: int, valor: int, status: str = "realizado", conta_no_saldo: bool = True
) -> Movimento:
    return Movimento(categoria, "entrada", valor, status, conta_no_saldo)


def saida(
    categoria: int, valor: int, status: str = "realizado", conta_no_saldo: bool = True
) -> Movimento:
    return Movimento(categoria, "saida", valor, status, conta_no_saldo)


def test_sem_movimentos() -> None:
    assert resumir([]) == Resumo(entradas=0, saidas=0, saldo=0, por_categoria={})


def test_totais_e_saldo() -> None:
    # US1.1
    resumo = resumir(
        [
            entrada(SALARIO, 500_000),
            entrada(EXTRA, 30_000),
            saida(ALIMENTACAO, 80_000),
            saida(MORADIA, 150_000),
        ]
    )
    assert (resumo.entradas, resumo.saidas, resumo.saldo) == (530_000, 230_000, 300_000)


def test_previsto_nao_conta() -> None:
    resumo = resumir([entrada(SALARIO, 500_000), saida(ALIMENTACAO, 10_000, status="previsto")])
    assert (resumo.saidas, resumo.saldo) == (0, 500_000)
    assert ALIMENTACAO not in resumo.por_categoria


def test_fora_do_saldo_nao_conta() -> None:
    resumo = resumir([entrada(SALARIO, 500_000), saida(ALIMENTACAO, 10_000, conta_no_saldo=False)])
    assert (resumo.saidas, resumo.saldo) == (0, 500_000)
    assert ALIMENTACAO not in resumo.por_categoria


def test_saldo_negativo() -> None:
    assert resumir([entrada(SALARIO, 100_000), saida(MORADIA, 150_000)]).saldo == -50_000


def test_so_salario() -> None:
    assert resumir([entrada(SALARIO, 500_000)]) == Resumo(
        entradas=500_000, saidas=0, saldo=500_000, por_categoria={SALARIO: 500_000}
    )


def test_total_por_categoria() -> None:
    # US2.1
    resumo = resumir(
        [
            saida(ALIMENTACAO, 80_000),
            saida(ALIMENTACAO, 20_000),
            saida(MORADIA, 150_000),
        ]
    )
    assert resumo.por_categoria == {ALIMENTACAO: 100_000, MORADIA: 150_000}


def test_somas_por_categoria_fecham_com_os_totais() -> None:
    movimentos = [
        entrada(SALARIO, 500_001),
        entrada(EXTRA, 3),
        saida(ALIMENTACAO, 7),
        saida(ALIMENTACAO, 11),
        saida(MORADIA, 99_999),
        saida(MORADIA, 5, status="previsto"),
    ]
    resumo = resumir(movimentos)
    tipo = {m.categoria_id: m.tipo for m in movimentos}
    soma_entradas = sum(v for c, v in resumo.por_categoria.items() if tipo[c] == "entrada")
    soma_saidas = sum(v for c, v in resumo.por_categoria.items() if tipo[c] == "saida")
    assert (soma_entradas, soma_saidas) == (resumo.entradas, resumo.saidas)
    assert resumo.saldo == resumo.entradas - resumo.saidas
