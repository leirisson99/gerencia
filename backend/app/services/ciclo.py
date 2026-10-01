from datetime import date

from sqlalchemy import ColumnElement, and_, func, select
from sqlalchemy.orm import Session

from app.domain.categoria import NOME_SALARIO
from app.domain.ciclo import Ciclo, ciclo_atual, ciclo_da_data, ciclo_mensal
from app.domain.usuario import ciclo_pelo_mes
from app.erros import ErroApi
from app.models import Categoria, Lancamento, Usuario
from app.models.lancamento import STATUS_REALIZADO


def travar_escritas(db: Session, usuario_id: int) -> str:
    """Serializa as escritas que mexem nos ciclos do usuário (lançamentos e previstos).

    Devolve o tipo de renda, lido sob o mesmo lock.
    """
    tipo = db.scalar(select(Usuario.tipo_renda).where(Usuario.id == usuario_id).with_for_update())
    assert tipo is not None, "usuário autenticado existe"
    return tipo


def tipo_renda_do_usuario(db: Session, usuario_id: int) -> str:
    tipo = db.scalar(select(Usuario.tipo_renda).where(Usuario.id == usuario_id))
    assert tipo is not None, "usuário autenticado existe"
    return tipo


def primeira_data_lancamento(db: Session, usuario_id: int) -> date | None:
    return db.scalar(select(func.min(Lancamento.data)).where(Lancamento.usuario_id == usuario_id))


def ciclo_da_data_do_usuario(db: Session, usuario_id: int, data: date, hoje: date) -> Ciclo | None:
    """Único ponto que decide a regra: mês do calendário (prestador) ou salário (os outros)."""
    if ciclo_pelo_mes(tipo_renda_do_usuario(db, usuario_id)):
        return ciclo_mensal(data, hoje, primeira_data_lancamento(db, usuario_id))
    return ciclo_da_data(datas_de_salario(db, usuario_id), data)


def ciclo_atual_do_usuario(db: Session, usuario_id: int, hoje: date) -> Ciclo | None:
    if ciclo_pelo_mes(tipo_renda_do_usuario(db, usuario_id)):
        return ciclo_mensal(hoje, hoje, primeira_data_lancamento(db, usuario_id))
    return ciclo_atual(datas_de_salario(db, usuario_id))


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


def obter_ciclo_atual(db: Session, usuario_id: int, hoje: date) -> Ciclo:
    ciclo = ciclo_atual_do_usuario(db, usuario_id, hoje)
    if ciclo is None:
        raise ErroApi(404, "sem_ciclo", "Lance seu salário para abrir o primeiro ciclo.")
    return ciclo


def obter_ciclo_da_data(db: Session, usuario_id: int, data: date, hoje: date) -> Ciclo:
    ciclo = ciclo_da_data_do_usuario(db, usuario_id, data, hoje)
    if ciclo is None:
        raise ErroApi(404, "sem_ciclo", "Não há ciclo nessa data.")
    return ciclo


def lancamentos_do_ciclo(db: Session, usuario_id: int, data: date, hoje: date) -> list[Lancamento]:
    return lancamentos_no_ciclo(db, usuario_id, obter_ciclo_da_data(db, usuario_id, data, hoje))


def lancamentos_no_ciclo(db: Session, usuario_id: int, ciclo: Ciclo) -> list[Lancamento]:
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
