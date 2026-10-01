from datetime import date

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.domain.lembrete import Origem, limite, situacao
from app.models import Lancamento
from app.models.lancamento import STATUS_PREVISTO
from app.schemas.lancamento import LancamentoOut
from app.schemas.lembrete import ItemLembrete, LembretesOut


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


def listar_lembretes(db: Session, usuario_id: int, hoje: date) -> LembretesOut:
    atrasados: list[ItemLembrete] = []
    a_vencer: list[ItemLembrete] = []
    for lancamento in pendencias_de_lancamento(db, usuario_id, hoje):
        sit = situacao(lancamento.data, hoje)
        if sit is None:  # a consulta já corta a janela
            continue
        item = ItemLembrete(
            origem=origem_do_lancamento(lancamento),
            situacao=sit,
            data=lancamento.data,
            lancamento=LancamentoOut.model_validate(lancamento),
        )
        (atrasados if sit == "atrasado" else a_vencer).append(item)
    return LembretesOut(hoje=hoje, limite=limite(hoje), atrasados=atrasados, a_vencer=a_vencer)
