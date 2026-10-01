"""US4 da spec 014: mais indicadores no resumo do administrador, sempre só contagens."""

from collections.abc import Callable
from datetime import date, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Cartela, Lancamento, Recorrencia, Servico, Usuario
from tests.api.conftest import USUARIOS
from tests.conftest import SENHA_PADRAO, RelogioFixo

RESUMO = "/api/v1/admin/resumo"


def resumo(cliente: TestClient) -> dict:
    resposta = cliente.get(RESUMO)
    assert resposta.status_code == 200
    return resposta.json()


# --- Cadastros por mês ---------------------------------------------------------------------


def test_cadastros_por_mes_sem_o_admin(
    cliente_admin: TestClient,
    usuarios: dict[str, Usuario],
    criar_usuario: Callable[..., Usuario],
    relogio: RelogioFixo,
) -> None:
    criar_usuario(email="julho@exemplo.com", criado_em=relogio.agora - timedelta(days=70))
    criar_usuario(email="antigo@exemplo.com", criado_em=relogio.agora - timedelta(days=400))

    cadastros = resumo(cliente_admin)["cadastros_por_mes"]

    assert len(cadastros) == 12
    assert cadastros[-1] == {"mes": "2026-09", "quantidade": 3}  # Ana, Bia e Caio
    assert cadastros[-3] == {"mes": "2026-07", "quantidade": 1}
    assert cadastros[-2] == {"mes": "2026-08", "quantidade": 0}
    assert sum(c["quantidade"] for c in cadastros) == 4  # o de 400 dias fica fora


# --- Engajamento ---------------------------------------------------------------------------


def test_ativas_em_7_e_30_dias(
    cliente_admin: TestClient,
    usuarios: dict[str, Usuario],
    criar_usuario: Callable[..., Usuario],
    relogio: RelogioFixo,
    db: Session,
) -> None:
    usuarios["ana"].ultimo_acesso_em = relogio.agora - timedelta(days=2)
    usuarios["bia"].ultimo_acesso_em = relogio.agora - timedelta(days=10)
    usuarios["caio"].ultimo_acesso_em = relogio.agora - timedelta(days=40)
    criar_usuario(email="nunca@exemplo.com")  # nunca entrou
    db.commit()

    engajamento = resumo(cliente_admin)["engajamento"]

    # O admin acabou de entrar, mas não conta.
    assert engajamento["ativas_7_dias"] == 1
    assert engajamento["ativas_30_dias"] == 2


def test_contas_com_lancamento(
    cliente_admin: TestClient, usuarios: dict[str, Usuario], lancar: Callable[..., Lancamento]
) -> None:
    lancar(usuarios["ana"], "entrada", date(2026, 9, 5))
    lancar(usuarios["ana"], "saida", date(2026, 9, 6))
    lancar(usuarios["bia"], "saida", date(2026, 9, 7), status="previsto")

    assert resumo(cliente_admin)["engajamento"]["com_lancamento"] == 2


# --- Último acesso -------------------------------------------------------------------------


def test_login_registra_o_ultimo_acesso_uma_vez_por_dia(
    usuarios: dict[str, Usuario],
    novo_client: Callable[[], TestClient],
    relogio: RelogioFixo,
    db: Session,
) -> None:
    login = {"email": "ana@exemplo.com", "senha": SENHA_PADRAO}
    inicio = relogio.agora

    assert novo_client().post("/api/v1/auth/login", json=login).status_code == 200
    db.refresh(usuarios["ana"])
    assert usuarios["ana"].ultimo_acesso_em == inicio

    relogio.avancar(hours=2)  # 14h em São Paulo: mesmo dia
    novo_client().post("/api/v1/auth/login", json=login)
    db.refresh(usuarios["ana"])
    assert usuarios["ana"].ultimo_acesso_em == inicio

    relogio.avancar(days=1)
    novo_client().post("/api/v1/auth/login", json=login)
    db.refresh(usuarios["ana"])
    assert usuarios["ana"].ultimo_acesso_em == relogio.agora


def test_uso_da_sessao_registra_o_ultimo_acesso(
    client: TestClient,
    usuarios: dict[str, Usuario],
    logar: Callable[[TestClient, Usuario], str],
    relogio: RelogioFixo,
    db: Session,
) -> None:
    logar(client, usuarios["ana"])
    relogio.avancar(days=3)

    assert client.get("/api/v1/me").status_code == 200

    db.refresh(usuarios["ana"])
    assert usuarios["ana"].ultimo_acesso_em == relogio.agora


def test_ultimo_acesso_nao_aparece_por_conta(
    cliente_admin: TestClient, usuarios: dict[str, Usuario]
) -> None:
    for rota in (USUARIOS, RESUMO, f"{USUARIOS}?situacao=ativos"):
        assert "ultimo_acesso" not in cliente_admin.get(rota).text


# --- Lançamentos importados × manuais -------------------------------------------------------


def test_importados_e_manuais(
    cliente_admin: TestClient, usuarios: dict[str, Usuario], lancar: Callable[..., Lancamento]
) -> None:
    lancar(usuarios["ana"], "saida", date(2026, 9, 5), id_externo="ofx-1")
    lancar(usuarios["ana"], "saida", date(2026, 9, 6), id_externo="ofx-2")
    lancar(usuarios["bia"], "entrada", date(2026, 9, 7))

    lancamentos = resumo(cliente_admin)["lancamentos"]

    assert (lancamentos["importados"], lancamentos["manuais"]) == (2, 1)


# --- Uso das funcionalidades ---------------------------------------------------------------


def test_uso_das_funcionalidades_conta_contas_distintas(
    cliente_admin: TestClient,
    usuarios: dict[str, Usuario],
    lancar: Callable[..., Lancamento],
    endividar: Callable[[Usuario, str], None],
    db: Session,
) -> None:
    ana, bia, caio = usuarios["ana"], usuarios["bia"], usuarios["caio"]
    saida = lancar(ana, "saida", date(2026, 9, 1))
    for descricao in ("Aluguel", "Internet"):  # duas recorrências, uma conta
        db.add(
            Recorrencia(
                usuario_id=ana.id,
                categoria_id=saida.categoria_id,
                descricao=descricao,
                valor=100_000,
                tipo="saida",
                dia=5,
            )
        )
    endividar(ana, "pix")
    endividar(bia, "boleto")
    db.add(Cartela(usuario_id=caio.id, nome="Viagem", meta=100_000, valor_base=1_000))
    entrada = lancar(bia, "entrada", date(2026, 10, 10), status="previsto")
    db.add(
        Servico(
            usuario_id=bia.id,
            categoria_id=entrada.categoria_id,
            cliente="Loja",
            valor=50_000,
            data_prevista=date(2026, 10, 10),
            lancamento_id=entrada.id,
        )
    )
    lancar(caio, "saida", date(2026, 9, 3), id_externo="ofx-1")
    lancar(caio, "saida", date(2026, 9, 4), id_externo="ofx-2")
    db.flush()

    uso = resumo(cliente_admin)["uso_funcionalidades"]

    assert uso == [
        {"funcionalidade": "recorrencias", "contas": 1},
        {"funcionalidade": "dividas", "contas": 2},
        {"funcionalidade": "cartelas", "contas": 1},
        {"funcionalidade": "servicos", "contas": 1},
        {"funcionalidade": "importacao", "contas": 1},
    ]


# --- Tipo de renda -------------------------------------------------------------------------


def test_contas_por_tipo_de_renda(
    cliente_admin: TestClient,
    usuarios: dict[str, Usuario],
    criar_usuario: Callable[..., Usuario],
) -> None:
    criar_usuario(email="carlos@exemplo.com", tipo_renda="prestador")
    criar_usuario(email="duda@exemplo.com", tipo_renda="clt_prestador")
    criar_usuario(email="eva@exemplo.com", tipo_renda="prestador")

    assert resumo(cliente_admin)["por_tipo_renda"] == {
        "clt": 3,
        "prestador": 2,
        "clt_prestador": 1,
    }


def test_resumo_vazio_traz_os_blocos_novos_zerados(cliente_admin: TestClient) -> None:
    corpo = resumo(cliente_admin)

    assert corpo["engajamento"] == {"ativas_7_dias": 0, "ativas_30_dias": 0, "com_lancamento": 0}
    assert corpo["por_tipo_renda"] == {"clt": 0, "prestador": 0, "clt_prestador": 0}
    assert [u["contas"] for u in corpo["uso_funcionalidades"]] == [0, 0, 0, 0, 0]
    assert all(c["quantidade"] == 0 for c in corpo["cadastros_por_mes"])
