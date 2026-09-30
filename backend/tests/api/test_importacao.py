import base64
from collections.abc import Callable
from pathlib import Path
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Lancamento
from tests.conftest import Conta

URL = "/api/v1/importacoes"
FIXTURES = Path(__file__).parent.parent / "domain" / "fixtures" / "extratos"
# hoje (relógio dos testes): 28/09/2026. inter.ofx: salário 05/09, padaria 06/09, aluguel 06/09.


def b64(conteudo: bytes) -> str:
    return base64.b64encode(conteudo).decode()


def arquivo(nome: str) -> str:
    return b64((FIXTURES / nome).read_bytes())


def pdf_com_linhas(linhas: list[str]) -> bytes:
    """PDF mínimo com uma linha de texto por item (Helvetica, WinAnsi)."""
    conteudo = ["BT", "/F1 10 Tf"]
    for i, texto in enumerate(linhas):
        escapado = texto.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        conteudo.append(f"1 0 0 1 30 {750 - 20 * i} Tm ({escapado}) Tj")
    conteudo.append("ET")
    stream = "\n".join(conteudo).encode("cp1252")
    objetos = [
        b"<</Type/Catalog/Pages 2 0 R>>",
        b"<</Type/Pages/Kids[3 0 R]/Count 1>>",
        b"<</Type/Page/Parent 2 0 R/MediaBox[0 0 600 800]"
        b"/Resources<</Font<</F1 5 0 R>>>>/Contents 4 0 R>>",
        b"<</Length %d>>stream\n" % len(stream) + stream + b"\nendstream",
        b"<</Type/Font/Subtype/Type1/BaseFont/Helvetica/Encoding/WinAnsiEncoding>>",
    ]
    saida = bytearray(b"%PDF-1.4\n")
    posicoes = []
    for numero, objeto in enumerate(objetos, start=1):
        posicoes.append(len(saida))
        saida += b"%d 0 obj\n" % numero + objeto + b"\nendobj\n"
    inicio_xref = len(saida)
    saida += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objetos) + 1)
    for posicao in posicoes:
        saida += b"%010d 00000 n \n" % posicao
    saida += b"trailer\n<</Size %d/Root 1 0 R>>\nstartxref\n%d\n%%%%EOF\n" % (
        len(objetos) + 1,
        inicio_xref,
    )
    return bytes(saida)


def previa(client: TestClient, **dados: Any) -> httpx.Response:
    corpo = {"banco": "inter", "formato": "ofx", "arquivo_base64": arquivo("inter.ofx")}
    corpo.update(dados)
    return client.post(f"{URL}/previa", json=corpo)


def linhas_da_previa(client: TestClient, **dados: Any) -> list[dict[str, Any]]:
    resposta = previa(client, **dados)
    assert resposta.status_code == 200, resposta.text
    return resposta.json()["linhas"]


def confirmacao(linhas: list[dict[str, Any]], categorias: list[int]) -> dict[str, Any]:
    return {
        "linhas": [
            {
                "id_externo": linha["id_externo"],
                "data": linha["data"],
                "valor": linha["valor"],
                "tipo": linha["tipo"],
                "descricao": linha["descricao"],
                "categoria_id": categoria,
            }
            for linha, categoria in zip(linhas, categorias, strict=True)
        ]
    }


def lancar(client: TestClient, conta: Conta, categoria: str, data: str, valor: int, **extra: Any):
    resposta = client.post(
        "/api/v1/lancamentos",
        json={"valor": valor, "categoria_id": conta.categorias[categoria], "data": data, **extra},
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


@pytest.fixture
def conta(client: TestClient, criar_conta: Callable[..., Conta]) -> Conta:
    return criar_conta(client)


@pytest.fixture
def salario(client: TestClient, conta: Conta) -> None:
    lancar(client, conta, "Salário", "2026-09-01", 500_000)


def categorias_do_inter(conta: Conta) -> list[int]:
    c = conta.categorias
    return [c["Renda extra"], c["Alimentação"], c["Moradia"]]


# --- Bancos ----------------------------------------------------------------------------------


def test_lista_os_bancos(client: TestClient, conta: Conta) -> None:
    bancos = client.get(f"{URL}/bancos").json()
    assert [b["codigo"] for b in bancos] == [
        "inter",
        "itau",
        "mercado_pago",
        "neon",
        "nubank",
        "outro",
    ]
    por_codigo = {b["codigo"]: b for b in bancos}
    assert por_codigo["nubank"] == {
        "codigo": "nubank",
        "nome": "Nubank",
        "formatos": ["ofx", "csv", "pdf"],
    }
    assert por_codigo["mercado_pago"]["formatos"] == ["pdf"]
    assert por_codigo["outro"]["formatos"] == ["ofx", "csv_generico"]


def test_rotas_exigem_sessao(client: TestClient) -> None:
    assert client.get(f"{URL}/bancos").status_code == 401
    assert previa(client).status_code == 401
    assert client.post(URL, json={"linhas": []}).status_code == 401


# --- US1: prévia e confirmação -----------------------------------------------------------------


def test_previa_le_o_extrato_e_nao_grava(
    client: TestClient, conta: Conta, salario: None, db: Session
) -> None:
    resposta = previa(client)

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert [(lin["data"], lin["valor"], lin["tipo"]) for lin in corpo["linhas"]] == [
        ("2026-09-05", 500_000, "entrada"),
        ("2026-09-06", 4_590, "saida"),
        ("2026-09-06", 123_456, "saida"),
    ]
    assert corpo["linhas"][1]["descricao"] == "Pix enviado: Padaria Central"
    assert corpo["linhas"][0]["id_externo"] == "inter:ofx:202609050001"
    assert {lin["situacao"] for lin in corpo["linhas"]} == {"nova"}
    assert corpo["resumo"] == {
        "nova": 3,
        "ja_importada": 0,
        "possivel_duplicada": 0,
        "antes_do_primeiro_ciclo": 0,
        "invalida": 0,
    }
    importados = db.scalars(select(Lancamento).where(Lancamento.id_externo.is_not(None))).all()
    assert importados == []


def test_confirmar_cria_lancamentos_realizados(
    client: TestClient, conta: Conta, salario: None
) -> None:
    linhas = linhas_da_previa(client)

    resposta = client.post(URL, json=confirmacao(linhas, categorias_do_inter(conta)))

    assert resposta.status_code == 201, resposta.text
    corpo = resposta.json()
    assert (corpo["criados"], corpo["ignoradas"]) == (3, 0)
    aluguel = client.get(f"/api/v1/lancamentos/{corpo['lancamento_ids'][2]}").json()
    assert aluguel["valor"] == 123_456
    assert aluguel["tipo"] == "saida"
    assert aluguel["status"] == "realizado"
    assert aluguel["categoria_id"] == conta.categorias["Moradia"]
    assert aluguel["descricao"] == "Pagamento de boleto: Aluguel"
    assert aluguel["importado"] is True
    resumo = client.get("/api/v1/ciclos/2026-09-01/resumo").json()
    assert (resumo["entradas"], resumo["saidas"]) == (1_000_000, 128_046)


def test_desmarcar_linhas(client: TestClient, conta: Conta, salario: None) -> None:
    linhas = linhas_da_previa(client)

    resposta = client.post(URL, json=confirmacao(linhas[1:2], [conta.categorias["Alimentação"]]))

    assert resposta.json()["criados"] == 1
    lancamentos = client.get("/api/v1/ciclos/2026-09-01/lancamentos").json()
    assert sorted(lanc["valor"] for lanc in lancamentos) == [4_590, 500_000]


def test_lancamento_manual_nao_e_importado(client: TestClient, conta: Conta, salario: None) -> None:
    manual = lancar(client, conta, "Lazer", "2026-09-10", 1_000)
    assert manual["importado"] is False


def test_categoria_de_tipo_diferente_recusa_o_lote(
    client: TestClient, conta: Conta, salario: None
) -> None:
    linhas = linhas_da_previa(client)
    categorias = categorias_do_inter(conta)
    categorias[0] = conta.categorias["Alimentação"]  # entrada numa categoria de saída

    resposta = client.post(URL, json=confirmacao(linhas, categorias))

    assert resposta.status_code == 422
    assert resposta.json()["erro"]["campos"] == {
        "linhas.0.categoria_id": "A linha é de entrada; escolha uma categoria de entrada."
    }
    assert len(client.get("/api/v1/ciclos/2026-09-01/lancamentos").json()) == 1


def test_categoria_inativa_recusa_o_lote(client: TestClient, conta: Conta, salario: None) -> None:
    client.patch(f"/api/v1/categorias/{conta.categorias['Moradia']}", json={"ativa": False})
    linhas = linhas_da_previa(client)

    resposta = client.post(URL, json=confirmacao(linhas, categorias_do_inter(conta)))

    assert resposta.status_code == 422
    assert resposta.json()["erro"]["campos"] == {"linhas.2.categoria_id": "Categoria inativa."}


@pytest.mark.parametrize(
    ("alteracao", "campo"),
    [
        ({"valor": 10.5}, "linhas.0.valor"),
        ({"valor": 0}, "linhas.0.valor"),
        ({"tipo": "transferencia"}, "linhas.0.tipo"),
        ({"id_externo": ""}, "linhas.0.id_externo"),
        ({"extra": 1}, "linhas.0.extra"),
    ],
)
def test_validacao_das_linhas(
    client: TestClient, conta: Conta, salario: None, alteracao: dict[str, Any], campo: str
) -> None:
    corpo = confirmacao(linhas_da_previa(client)[:1], [conta.categorias["Renda extra"]])
    corpo["linhas"][0].update(alteracao)

    resposta = client.post(URL, json=corpo)

    assert resposta.status_code == 422
    assert campo in resposta.json()["erro"]["campos"]


def test_lote_vazio_e_recusado(client: TestClient, conta: Conta) -> None:
    assert client.post(URL, json={"linhas": []}).status_code == 422


def test_categoria_de_outro_usuario(
    client: TestClient,
    novo_client: Callable[[], TestClient],
    criar_conta: Callable[..., Conta],
    conta: Conta,
    salario: None,
) -> None:
    bia = criar_conta(novo_client(), email="bia@exemplo.com")
    linhas = linhas_da_previa(client)

    resposta = client.post(URL, json=confirmacao(linhas[:1], [bia.categorias["Renda extra"]]))

    assert resposta.status_code == 404


@pytest.mark.parametrize(
    ("dados", "status", "codigo"),
    [
        ({"arquivo_base64": "@@@ não é base64"}, 422, "extrato_invalido"),
        ({"arquivo_base64": b64(b"Data,Valor\n01/09/2026,10.00\n")}, 422, "extrato_invalido"),
        ({"formato": "pdf", "arquivo_base64": b64(b"isto nao e um pdf")}, 422, "extrato_invalido"),
        ({"arquivo_base64": b64(b"x" * (2 * 1024 * 1024 + 1))}, 413, "extrato_grande"),
    ],
)
def test_arquivo_recusado(
    client: TestClient, conta: Conta, dados: dict[str, Any], status: int, codigo: str
) -> None:
    resposta = previa(client, **dados)

    assert resposta.status_code == status
    assert resposta.json()["erro"]["codigo"] == codigo


# --- US3: sem duplicar -----------------------------------------------------------------------


def test_reimportar_nao_duplica(client: TestClient, conta: Conta, salario: None) -> None:
    linhas = linhas_da_previa(client)
    client.post(URL, json=confirmacao(linhas, categorias_do_inter(conta)))

    de_novo = linhas_da_previa(client)
    assert {lin["situacao"] for lin in de_novo} == {"ja_importada"}

    resposta = client.post(URL, json=confirmacao(de_novo, categorias_do_inter(conta)))
    assert resposta.status_code == 201
    assert (resposta.json()["criados"], resposta.json()["ignoradas"]) == (0, 3)


def test_linha_repetida_no_lote_conta_uma_vez(
    client: TestClient, conta: Conta, salario: None
) -> None:
    linha = linhas_da_previa(client)[1]
    alimentacao = conta.categorias["Alimentação"]

    resposta = client.post(URL, json=confirmacao([linha, linha], [alimentacao, alimentacao]))

    assert (resposta.json()["criados"], resposta.json()["ignoradas"]) == (1, 1)


def test_lancamento_manual_igual_vira_possivel_duplicada(
    client: TestClient, conta: Conta, salario: None
) -> None:
    lancar(client, conta, "Alimentação", "2026-09-06", 4_590)

    situacoes = [lin["situacao"] for lin in linhas_da_previa(client)]

    assert situacoes == ["nova", "possivel_duplicada", "nova"]


def test_dois_gastos_iguais_no_mesmo_dia(client: TestClient, conta: Conta, salario: None) -> None:
    csv = "data;descricao;valor\n10/09/2026;Café;-8,00\n10/09/2026;Café;-8,00\n"
    mapeamento = {
        "separador": ";",
        "coluna_data": 0,
        "formato_data": "dd/mm/aaaa",
        "coluna_descricao": 1,
        "coluna_valor": 2,
        "separador_decimal": ",",
    }
    dados = {
        "banco": "outro",
        "formato": "csv_generico",
        "arquivo_base64": b64(csv.encode()),
        "mapeamento": mapeamento,
    }
    linhas = linhas_da_previa(client, **dados)
    assert len({lin["id_externo"] for lin in linhas}) == 2
    alimentacao = conta.categorias["Alimentação"]

    resposta = client.post(URL, json=confirmacao(linhas, [alimentacao, alimentacao]))

    assert resposta.json()["criados"] == 2
    assert {lin["situacao"] for lin in linhas_da_previa(client, **dados)} == {"ja_importada"}


def test_ja_importada_e_por_usuario(
    client: TestClient,
    novo_client: Callable[[], TestClient],
    criar_conta: Callable[..., Conta],
    conta: Conta,
    salario: None,
) -> None:
    client.post(URL, json=confirmacao(linhas_da_previa(client), categorias_do_inter(conta)))
    cliente_bia = novo_client()
    criar_conta(cliente_bia, email="bia@exemplo.com")

    situacoes = {lin["situacao"] for lin in linhas_da_previa(cliente_bia)}

    assert situacoes == {"nova"}


# --- US2: histórico e salários -----------------------------------------------------------------


def test_historico_sem_salario_abre_o_ciclo_pelo_lote(client: TestClient, conta: Conta) -> None:
    linhas = linhas_da_previa(client)
    assert {lin["situacao"] for lin in linhas} == {"nova"}  # o lote pode trazer o salário
    categorias = categorias_do_inter(conta)
    categorias[0] = conta.categorias["Salário"]

    resposta = client.post(URL, json=confirmacao(linhas, categorias))

    assert resposta.status_code == 201, resposta.text
    ciclo = client.get("/api/v1/ciclos/atual").json()
    assert (ciclo["inicio"], ciclo["fim"]) == ("2026-09-05", None)


def test_lote_sem_salario_para_usuario_sem_salario(client: TestClient, conta: Conta) -> None:
    linhas = linhas_da_previa(client)

    resposta = client.post(URL, json=confirmacao(linhas, categorias_do_inter(conta)))

    assert resposta.status_code == 409
    assert resposta.json()["erro"]["codigo"] == "salario_necessario"


def test_linha_antes_do_primeiro_salario(client: TestClient, conta: Conta) -> None:
    lancar(client, conta, "Salário", "2026-09-06", 500_000)

    linhas = linhas_da_previa(client)
    assert [lin["situacao"] for lin in linhas] == ["antes_do_primeiro_ciclo", "nova", "nova"]

    resposta = client.post(URL, json=confirmacao(linhas, categorias_do_inter(conta)))
    assert resposta.status_code == 409
    assert resposta.json()["erro"]["codigo"] == "antes_do_primeiro_ciclo"

    resposta = client.post(URL, json=confirmacao(linhas[1:], categorias_do_inter(conta)[1:]))
    assert resposta.status_code == 201


def _linha(id_externo: str, data: str, categoria_id: int, valor: int = 500_000) -> dict[str, Any]:
    return {
        "id_externo": id_externo,
        "data": data,
        "valor": valor,
        "tipo": "entrada",
        "descricao": "Salário",
        "categoria_id": categoria_id,
    }


def test_salario_futuro_no_lote(client: TestClient, conta: Conta) -> None:
    resposta = client.post(
        URL, json={"linhas": [_linha("t:1", "2026-10-01", conta.categorias["Salário"])]}
    )

    assert resposta.status_code == 422
    assert "linhas.0.data" in resposta.json()["erro"]["campos"]


def _previstos(client: TestClient, data_ciclo: str) -> list[dict[str, Any]]:
    lancamentos = client.get(f"/api/v1/ciclos/{data_ciclo}/lancamentos").json()
    return [lanc for lanc in lancamentos if lanc["recorrencia_id"] is not None]


def test_salario_do_passado_nao_gera_previstos(client: TestClient, conta: Conta) -> None:
    lancar(client, conta, "Salário", "2026-09-20", 500_000)
    client.post(
        "/api/v1/recorrencias",
        json={
            "descricao": "Internet",
            "valor": 10_000,
            "categoria_id": conta.categorias["Moradia"],
            "dia": 10,
        },
    )

    resposta = client.post(
        URL, json={"linhas": [_linha("t:1", "2026-08-20", conta.categorias["Salário"])]}
    )

    assert resposta.status_code == 201
    assert _previstos(client, "2026-08-20") == []
    assert len(_previstos(client, "2026-09-20")) == 1


def test_salario_mais_recente_gera_previstos_do_novo_ciclo(
    client: TestClient, conta: Conta, salario: None
) -> None:
    client.post(
        "/api/v1/recorrencias",
        json={
            "descricao": "Internet",
            "valor": 10_000,
            "categoria_id": conta.categorias["Moradia"],
            "dia": 10,
        },
    )

    resposta = client.post(
        URL, json={"linhas": [_linha("t:1", "2026-09-25", conta.categorias["Salário"])]}
    )

    assert resposta.status_code == 201
    [previsto] = _previstos(client, "2026-09-25")
    assert previsto["data"] == "2026-10-10"


# --- US4: bancos e formatos ------------------------------------------------------------------


@pytest.mark.parametrize(
    ("dados", "campo", "codigo"),
    [
        ({"banco": "banco_x"}, "banco", "validacao"),
        ({"banco": "mercado_pago", "formato": "ofx"}, "formato", "formato_indisponivel"),
        ({"banco": "outro", "formato": "csv_generico"}, "mapeamento", "validacao"),
        (
            {
                "mapeamento": {
                    "separador": ";",
                    "coluna_data": 0,
                    "formato_data": "dd/mm/aaaa",
                    "coluna_descricao": 1,
                    "coluna_valor": 2,
                    "separador_decimal": ",",
                }
            },
            "mapeamento",
            "validacao",
        ),
    ],
)
def test_banco_e_formato(
    client: TestClient, conta: Conta, dados: dict[str, Any], campo: str, codigo: str
) -> None:
    resposta = previa(client, **dados)

    assert resposta.status_code == 422
    assert resposta.json()["erro"]["codigo"] == codigo
    assert campo in resposta.json()["erro"]["campos"]


def test_mapeamento_sem_coluna_de_valor(client: TestClient, conta: Conta) -> None:
    resposta = previa(
        client,
        banco="outro",
        formato="csv_generico",
        mapeamento={
            "separador": ";",
            "coluna_data": 0,
            "formato_data": "dd/mm/aaaa",
            "coluna_descricao": 1,
            "coluna_credito": 2,
            "separador_decimal": ",",
        },
    )

    assert resposta.status_code == 422


@pytest.mark.parametrize(
    ("banco", "formato", "nome"),
    [
        ("nubank", "csv", "nubank.csv"),
        ("nubank", "ofx", "nubank.ofx"),
        ("inter", "csv", "inter.csv"),
    ],
)
def test_formatos_de_cada_banco(
    client: TestClient, conta: Conta, banco: str, formato: str, nome: str
) -> None:
    linhas = linhas_da_previa(client, banco=banco, formato=formato, arquivo_base64=arquivo(nome))

    assert len(linhas) >= 2
    assert all(lin["id_externo"].startswith(f"{banco}:{formato}:") for lin in linhas)


def test_pdf_do_banco_ponta_a_ponta(client: TestClient, conta: Conta, salario: None) -> None:
    pdf = pdf_com_linhas(
        [
            "data lançamentos valor (R$) saldo (R$)",
            "02/09/2026 SALDO ANTERIOR 10,00",
            "02/09/2026 PIX QRS PADARIA CE02/09 -12,50",
            "03/09/2026 REND PAGO APLIC AUT MAIS 0,07",
            "03/09/2026 SALDO DO DIA -2,43",
        ]
    )

    linhas = linhas_da_previa(client, banco="itau", formato="pdf", arquivo_base64=b64(pdf))

    assert [(lin["data"], lin["valor"], lin["tipo"], lin["descricao"]) for lin in linhas] == [
        ("2026-09-02", 1_250, "saida", "PIX QRS PADARIA CE02/09"),
        ("2026-09-03", 7, "entrada", "REND PAGO APLIC AUT MAIS"),
    ]


def test_pdf_de_outro_layout_e_recusado(client: TestClient, conta: Conta) -> None:
    pdf = pdf_com_linhas(["Extrato qualquer", "01/09/2026 Compra 10,00"])

    resposta = previa(client, banco="itau", formato="pdf", arquivo_base64=b64(pdf))

    assert resposta.status_code == 422
    assert resposta.json()["erro"]["codigo"] == "extrato_invalido"
    assert "OFX ou CSV" in resposta.json()["erro"]["mensagem"]


def test_pdf_sem_texto(client: TestClient, conta: Conta) -> None:
    resposta = previa(client, banco="itau", formato="pdf", arquivo_base64=b64(pdf_com_linhas([])))

    assert resposta.status_code == 422
    assert resposta.json()["erro"]["codigo"] == "pdf_sem_texto"


# --- US5: sugestão de categoria ----------------------------------------------------------------


def test_sugere_a_categoria_da_ultima_descricao_igual(
    client: TestClient, conta: Conta, salario: None
) -> None:
    lancar(client, conta, "Lazer", "2026-09-02", 1_000, descricao="PIX ENVIADO: padaria central")
    lancar(
        client, conta, "Alimentação", "2026-09-03", 1_000, descricao="Pix enviado: Padaria Central"
    )

    linhas = linhas_da_previa(client)

    assert linhas[1]["categoria_sugerida_id"] == conta.categorias["Alimentação"]
    assert linhas[2]["categoria_sugerida_id"] is None


def test_nao_sugere_categoria_desativada(client: TestClient, conta: Conta, salario: None) -> None:
    lancar(client, conta, "Lazer", "2026-09-02", 1_000, descricao="Pix enviado: Padaria Central")
    client.patch(f"/api/v1/categorias/{conta.categorias['Lazer']}", json={"ativa": False})

    assert linhas_da_previa(client)[1]["categoria_sugerida_id"] is None
