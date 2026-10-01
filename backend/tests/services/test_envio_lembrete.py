"""Feature 015: resumo diário por push, com um enviador falso (sem rede)."""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date
from typing import Any

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.lembrete import Contagem, Total, texto_resumo
from app.models import Categoria, EnvioLembrete, InscricaoPush, Lancamento, Usuario
from app.services.categoria import criar_categorias_iniciais
from app.services.envio_lembrete import ResultadoEnvio, enviar_lembretes_do_dia

HOJE = date(2026, 10, 14)  # quarta; a janela vai até sábado, 17/10


@dataclass
class EnviadorFalso:
    """Registra cada envio; o resultado por endpoint é configurável (padrão: ok)."""

    resultados: dict[str, ResultadoEnvio] = field(default_factory=dict)
    enviados: list[tuple[str, dict[str, Any]]] = field(default_factory=list)

    def enviar(self, inscricao: InscricaoPush, payload: dict[str, Any]) -> ResultadoEnvio:
        self.enviados.append((inscricao.endpoint, payload))
        return self.resultados.get(inscricao.endpoint, "ok")


@pytest.fixture
def enviador() -> EnviadorFalso:
    return EnviadorFalso()


@pytest.fixture
def novo_usuario(db: Session, criar_usuario: Callable[..., Usuario]) -> Callable[..., Usuario]:
    def _criar(email: str = "ana@exemplo.com", **campos: Any) -> Usuario:
        usuario = criar_usuario(email=email, tipo_renda="prestador", **campos)
        criar_categorias_iniciais(db, usuario.id)
        db.flush()
        return usuario

    return _criar


def categoria(db: Session, usuario: Usuario, nome: str) -> int:
    return db.scalars(
        select(Categoria.id).where(Categoria.usuario_id == usuario.id, Categoria.nome == nome)
    ).one()


def prever(
    db: Session,
    usuario: Usuario,
    data: date,
    tipo: str = "saida",
    conta_no_saldo: bool = True,
    descricao: str = "Aluguel do apartamento",
) -> None:
    db.add(
        Lancamento(
            usuario_id=usuario.id,
            categoria_id=categoria(db, usuario, "Moradia" if tipo == "saida" else "Renda extra"),
            data=data,
            valor=123_456,
            tipo=tipo,
            status="previsto",
            conta_no_saldo=conta_no_saldo,
            descricao=descricao,
        )
    )
    db.flush()


def inscrever(db: Session, usuario: Usuario, endpoint: str = "https://push.exemplo/ana-1") -> None:
    db.add(InscricaoPush(usuario_id=usuario.id, endpoint=endpoint, p256dh="p" * 87, auth="a" * 22))
    db.flush()


def endpoints(db: Session, usuario: Usuario) -> list[str]:
    return list(
        db.scalars(
            select(InscricaoPush.endpoint)
            .where(InscricaoPush.usuario_id == usuario.id)
            .order_by(InscricaoPush.endpoint)
        )
    )


def reservas(db: Session, usuario: Usuario) -> list[date]:
    return list(db.scalars(select(EnvioLembrete.dia).where(EnvioLembrete.usuario_id == usuario.id)))


def test_envia_resumo_so_com_contagens(
    db: Session, novo_usuario: Callable[..., Usuario], enviador: EnviadorFalso
) -> None:
    # US2.1
    ana = novo_usuario()
    prever(db, ana, date(2026, 10, 15))
    prever(db, ana, date(2026, 10, 17))
    prever(db, ana, date(2026, 10, 13), tipo="entrada", descricao="Loja da Maria — Site")
    inscrever(db, ana)

    relatorio = enviar_lembretes_do_dia(db, HOJE, enviador)

    esperado = texto_resumo(Contagem(contas=Total(a_vencer=2), valores=Total(atrasados=1)), HOJE)
    assert esperado is not None
    ((endpoint, payload),) = enviador.enviados
    assert endpoint == "https://push.exemplo/ana-1"
    assert payload == {"titulo": esperado.titulo, "corpo": esperado.corpo, "url": "/lembretes"}
    assert payload["corpo"] == "2 contas a pagar até sábado · 1 valor a receber, atrasado."
    texto = str(payload)
    for proibido in ("Aluguel", "Maria", "Moradia", "Renda", "1.234", "1234", "R$"):
        assert proibido not in texto
    assert relatorio.enviados == 1
    assert reservas(db, ana) == [HOJE]


def test_rodar_de_novo_no_mesmo_dia_nao_reenvia(
    db: Session, novo_usuario: Callable[..., Usuario], enviador: EnviadorFalso
) -> None:
    # US2.2
    ana = novo_usuario()
    prever(db, ana, HOJE)
    inscrever(db, ana)
    enviar_lembretes_do_dia(db, HOJE, enviador)

    relatorio = enviar_lembretes_do_dia(db, HOJE, enviador)

    assert len(enviador.enviados) == 1
    assert relatorio.ja_enviados == 1
    assert relatorio.enviados == 0


def test_no_dia_seguinte_envia_de_novo(
    db: Session, novo_usuario: Callable[..., Usuario], enviador: EnviadorFalso
) -> None:
    ana = novo_usuario()
    prever(db, ana, HOJE)
    inscrever(db, ana)
    enviar_lembretes_do_dia(db, HOJE, enviador)

    enviar_lembretes_do_dia(db, date(2026, 10, 15), enviador)

    assert len(enviador.enviados) == 2


def test_reserva_ja_existente_nao_envia(
    db: Session, novo_usuario: Callable[..., Usuario], enviador: EnviadorFalso
) -> None:
    # Outra execução do mesmo dia já reservou
    ana = novo_usuario()
    prever(db, ana, HOJE)
    inscrever(db, ana)
    db.add(EnvioLembrete(usuario_id=ana.id, dia=HOJE))
    db.flush()

    relatorio = enviar_lembretes_do_dia(db, HOJE, enviador)

    assert enviador.enviados == []
    assert relatorio.ja_enviados == 1


def test_sem_pendencias_nao_envia(
    db: Session, novo_usuario: Callable[..., Usuario], enviador: EnviadorFalso
) -> None:
    # US2.3: fora da janela, pago no cartão ou já realizado não contam
    ana = novo_usuario()
    prever(db, ana, date(2026, 10, 18))
    prever(db, ana, HOJE, conta_no_saldo=False)
    inscrever(db, ana)

    relatorio = enviar_lembretes_do_dia(db, HOJE, enviador)

    assert enviador.enviados == []
    assert relatorio.sem_pendencias == 1
    assert reservas(db, ana) == []


def test_sem_aparelho_e_ignorado(
    db: Session, novo_usuario: Callable[..., Usuario], enviador: EnviadorFalso
) -> None:
    ana = novo_usuario()
    prever(db, ana, HOJE)

    relatorio = enviar_lembretes_do_dia(db, HOJE, enviador)

    assert enviador.enviados == []
    assert relatorio.usuarios == 0


@pytest.mark.parametrize("campos", [{"ativo": False}, {"papel": "admin"}])
def test_conta_desativada_e_administrador_nao_recebem(
    db: Session,
    novo_usuario: Callable[..., Usuario],
    enviador: EnviadorFalso,
    campos: dict[str, Any],
) -> None:
    # FR-012
    usuario = novo_usuario(**campos)
    prever(db, usuario, HOJE)
    inscrever(db, usuario)

    relatorio = enviar_lembretes_do_dia(db, HOJE, enviador)

    assert enviador.enviados == []
    assert relatorio.usuarios == 0


def test_dois_aparelhos_recebem_o_mesmo_resumo(
    db: Session, novo_usuario: Callable[..., Usuario], enviador: EnviadorFalso
) -> None:
    # US2.4
    ana = novo_usuario()
    prever(db, ana, HOJE)
    inscrever(db, ana, "https://push.exemplo/ana-1")
    inscrever(db, ana, "https://push.exemplo/ana-2")

    enviar_lembretes_do_dia(db, HOJE, enviador)

    assert sorted(e for e, _ in enviador.enviados) == [
        "https://push.exemplo/ana-1",
        "https://push.exemplo/ana-2",
    ]
    assert enviador.enviados[0][1] == enviador.enviados[1][1]


def test_aparelho_expirado_e_removido_e_o_outro_recebe(
    db: Session, novo_usuario: Callable[..., Usuario], enviador: EnviadorFalso
) -> None:
    # US2.6, FR-013
    ana = novo_usuario()
    prever(db, ana, HOJE)
    inscrever(db, ana, "https://push.exemplo/ana-1")
    inscrever(db, ana, "https://push.exemplo/ana-2")
    enviador.resultados["https://push.exemplo/ana-1"] = "expirado"

    relatorio = enviar_lembretes_do_dia(db, HOJE, enviador)

    assert endpoints(db, ana) == ["https://push.exemplo/ana-2"]
    assert relatorio.removidos == 1
    assert relatorio.enviados == 1
    assert reservas(db, ana) == [HOJE]


def test_falha_em_todos_os_aparelhos_libera_o_dia(
    db: Session, novo_usuario: Callable[..., Usuario], enviador: EnviadorFalso
) -> None:
    # Edge case: falha temporária tenta de novo no mesmo dia
    ana = novo_usuario()
    prever(db, ana, HOJE)
    inscrever(db, ana)
    enviador.resultados["https://push.exemplo/ana-1"] = "falha"

    relatorio = enviar_lembretes_do_dia(db, HOJE, enviador)

    assert relatorio.falhas == 1
    assert reservas(db, ana) == []
    assert endpoints(db, ana) == ["https://push.exemplo/ana-1"]

    enviador.resultados.clear()
    relatorio = enviar_lembretes_do_dia(db, HOJE, enviador)

    assert relatorio.enviados == 1
    assert len(enviador.enviados) == 2


def test_cada_usuario_recebe_o_proprio_resumo(
    db: Session, novo_usuario: Callable[..., Usuario], enviador: EnviadorFalso
) -> None:
    # Isolamento: as contagens de Bia não entram no resumo de Ana
    ana = novo_usuario()
    bia = novo_usuario("bia@exemplo.com")
    prever(db, ana, HOJE)
    prever(db, bia, HOJE)
    prever(db, bia, HOJE)
    inscrever(db, ana, "https://push.exemplo/ana-1")
    inscrever(db, bia, "https://push.exemplo/bia-1")

    relatorio = enviar_lembretes_do_dia(db, HOJE, enviador)

    corpos = dict((e, p["corpo"]) for e, p in enviador.enviados)
    assert corpos == {
        "https://push.exemplo/ana-1": "1 conta a pagar até sábado.",
        "https://push.exemplo/bia-1": "2 contas a pagar até sábado.",
    }
    assert relatorio.usuarios == relatorio.enviados == 2
