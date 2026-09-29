from datetime import date

from sqlalchemy import ColumnElement, and_, select
from sqlalchemy.orm import Session

from app.domain.categoria import NOME_SALARIO
from app.domain.ciclo import Ciclo, ciclo_atual, ciclo_da_data
from app.erros import ErroApi
from app.models import Categoria, Lancamento
from app.models.lancamento import STATUS_REALIZADO


def condicao_salario() -> ColumnElement[bool]:
    """Lançamento que abre ciclo: categoria de sistema "Salário" e realizado.

    Exige o `join` com `Categoria`.
    """
    return and_(
        Categoria.sistema,
        Categoria.nome == NOME_SALARIO,
        Lancamento.status == STATUS_REALIZADO,
    )


def datas_de_salario(db: Session, usuario_id: int, ignorar_id: int | None = None) -> list[date]:
    consulta = (
        select(Lancamento.data)
        .join(Categoria, Lancamento.categoria_id == Categoria.id)
        .where(Lancamento.usuario_id == usuario_id, condicao_salario())
    )
    if ignorar_id is not None:
        consulta = consulta.where(Lancamento.id != ignorar_id)
    return list(db.scalars(consulta))


def obter_ciclo_atual(db: Session, usuario_id: int) -> Ciclo:
    ciclo = ciclo_atual(datas_de_salario(db, usuario_id))
    if ciclo is None:
        raise ErroApi(404, "sem_ciclo", "Lance seu salário para abrir o primeiro ciclo.")
    return ciclo


def obter_ciclo_da_data(db: Session, usuario_id: int, data: date) -> Ciclo:
    ciclo = ciclo_da_data(datas_de_salario(db, usuario_id), data)
    if ciclo is None:
        raise ErroApi(404, "sem_ciclo", "Não há ciclo nessa data.")
    return ciclo


def lancamentos_do_ciclo(db: Session, usuario_id: int, data: date) -> list[Lancamento]:
    ciclo = obter_ciclo_da_data(db, usuario_id, data)
    consulta = select(Lancamento).where(
        Lancamento.usuario_id == usuario_id, Lancamento.data >= ciclo.inicio
    )
    if ciclo.fim is not None:
        consulta = consulta.where(Lancamento.data <= ciclo.fim)
    return list(db.scalars(consulta.order_by(Lancamento.data, Lancamento.id)))


def sugestao_salario(db: Session, usuario_id: int) -> int | None:
    """Valor do salário de data mais recente."""
    return db.scalar(
        select(Lancamento.valor)
        .join(Categoria, Lancamento.categoria_id == Categoria.id)
        .where(Lancamento.usuario_id == usuario_id, condicao_salario())
        .order_by(Lancamento.data.desc(), Lancamento.id.desc())
        .limit(1)
    )
