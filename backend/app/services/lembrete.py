from datetime import date, datetime

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.domain.lembrete import Origem, limite, situacao
from app.erros import ErroApi
from app.models import Lancamento, Lembrete
from app.models.lancamento import STATUS_PREVISTO
from app.schemas.lancamento import LancamentoOut
from app.schemas.lembrete import (
    ItemLembrete,
    LembreteLivreIn,
    LembreteLivreOut,
    LembreteLivrePatch,
    LembretesOut,
)


def origem_do_lancamento(lancamento: Lancamento) -> Origem:
    return "valor" if lancamento.tipo == "entrada" else "conta"


def pendencias_de_lancamento(db: Session, usuario_id: int, hoje: date) -> list[Lancamento]:
    """Previstos até o fim da janela, inclusive os atrasados.

    Saídas fora do saldo (pagas no cartão) ficam de fora: quem é pago é a fatura.
    """
    return list(
        db.scalars(
            select(Lancamento)
            .where(
                Lancamento.usuario_id == usuario_id,
                Lancamento.status == STATUS_PREVISTO,
                Lancamento.data <= limite(hoje),
                or_(Lancamento.tipo == "entrada", Lancamento.conta_no_saldo.is_(True)),
            )
            .order_by(Lancamento.data, Lancamento.id)
        )
    )


def livres_pendentes(db: Session, usuario_id: int, hoje: date) -> list[Lembrete]:
    """Lembretes livres não concluídos até o fim da janela, inclusive os atrasados."""
    return list(
        db.scalars(
            select(Lembrete)
            .where(
                Lembrete.usuario_id == usuario_id,
                Lembrete.concluido_em.is_(None),
                Lembrete.data <= limite(hoje),
            )
            .order_by(Lembrete.data, Lembrete.id)
        )
    )


def listar_lembretes(db: Session, usuario_id: int, hoje: date) -> LembretesOut:
    itens = [
        ItemLembrete(
            origem=origem_do_lancamento(lancamento),
            situacao=sit,
            data=lancamento.data,
            lancamento=LancamentoOut.model_validate(lancamento),
        )
        for lancamento in pendencias_de_lancamento(db, usuario_id, hoje)
        if (sit := situacao(lancamento.data, hoje)) is not None
    ] + [
        ItemLembrete(
            origem="livre",
            situacao=sit,
            data=livre.data,
            lembrete=LembreteLivreOut.model_validate(livre),
        )
        for livre in livres_pendentes(db, usuario_id, hoje)
        if (sit := situacao(livre.data, hoje)) is not None
    ]
    # Por data; no mesmo dia, os lançamentos antes dos lembretes livres (ordem estável).
    itens.sort(key=lambda item: item.data)
    return LembretesOut(
        hoje=hoje,
        limite=limite(hoje),
        atrasados=[i for i in itens if i.situacao == "atrasado"],
        a_vencer=[i for i in itens if i.situacao == "a_vencer"],
    )


# --- lembretes livres ----------------------------------------------------------------------------


def _obter_livre(db: Session, usuario_id: int, lembrete_id: int) -> Lembrete:
    lembrete = db.scalar(
        select(Lembrete).where(Lembrete.id == lembrete_id, Lembrete.usuario_id == usuario_id)
    )
    if lembrete is None:
        raise ErroApi(404, "nao_encontrado", "Lembrete não encontrado.")
    return lembrete


def listar_livres(db: Session, usuario_id: int) -> list[Lembrete]:
    return list(
        db.scalars(
            select(Lembrete)
            .where(Lembrete.usuario_id == usuario_id)
            .order_by(Lembrete.data, Lembrete.id)
        )
    )


def criar_livre(db: Session, usuario_id: int, dados: LembreteLivreIn, agora: datetime) -> Lembrete:
    lembrete = Lembrete(usuario_id=usuario_id, texto=dados.texto, data=dados.data, criado_em=agora)
    db.add(lembrete)
    db.commit()
    return lembrete


def editar_livre(
    db: Session, usuario_id: int, lembrete_id: int, dados: LembreteLivrePatch, agora: datetime
) -> Lembrete:
    lembrete = _obter_livre(db, usuario_id, lembrete_id)
    if dados.texto is not None:
        lembrete.texto = dados.texto
    if dados.data is not None:
        lembrete.data = dados.data
    if dados.concluido is not None and dados.concluido != lembrete.concluido:
        lembrete.concluido_em = agora if dados.concluido else None
    db.commit()
    return lembrete


def excluir_livre(db: Session, usuario_id: int, lembrete_id: int) -> None:
    db.delete(_obter_livre(db, usuario_id, lembrete_id))
    db.commit()
