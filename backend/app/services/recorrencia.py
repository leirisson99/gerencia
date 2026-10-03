from collections.abc import Iterable
from datetime import date, datetime

from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from app.domain.ciclo import Ciclo, ciclo_mensal
from app.domain.recorrencia import data_prevista
from app.domain.usuario import CARTEIRA_PADRAO, Carteira, ciclo_pelo_mes
from app.erros import MENSAGEM_VALIDACAO, ErroApi
from app.models import Categoria, Lancamento, Recorrencia
from app.models.lancamento import STATUS_PREVISTO
from app.schemas.recorrencia import RecorrenciaIn, RecorrenciaPatch
from app.services.categoria import obter_categoria_ativa
from app.services.ciclo import (
    ciclo_atual_do_usuario,
    exigir_carteira,
    tipo_renda_do_usuario,
    travar_escritas,
)
from app.services.evento_uso import registrar


def _categoria_de_recorrencia(db: Session, usuario_id: int, categoria_id: int) -> Categoria:
    categoria = obter_categoria_ativa(db, usuario_id, categoria_id)
    if categoria.e_salario:
        raise ErroApi(
            422,
            "validacao",
            MENSAGEM_VALIDACAO,
            campos={"categoria_id": "O salário é lançado à mão, não como recorrência."},
        )
    return categoria


def listar_recorrencias(
    db: Session, usuario_id: int, carteira: Carteira | None = None
) -> list[Recorrencia]:
    """Todas, ou só as de uma carteira."""
    consulta = select(Recorrencia).where(Recorrencia.usuario_id == usuario_id)
    if carteira is not None:
        consulta = consulta.where(Recorrencia.carteira == carteira)
    return list(
        db.scalars(consulta.order_by(Recorrencia.dia, Recorrencia.descricao, Recorrencia.id))
    )


def obter_recorrencia(db: Session, usuario_id: int, recorrencia_id: int) -> Recorrencia:
    recorrencia = db.scalar(
        select(Recorrencia).where(
            Recorrencia.id == recorrencia_id, Recorrencia.usuario_id == usuario_id
        )
    )
    if recorrencia is None:
        raise ErroApi(404, "nao_encontrado", "Recorrência não encontrada.")
    return recorrencia


def gerar_previstos(
    db: Session,
    usuario_id: int,
    ciclo: Ciclo,
    agora: datetime,
    recorrencias: Iterable[Recorrencia] | None = None,
    carteira: Carteira = CARTEIRA_PADRAO,
) -> None:
    """Um previsto por recorrência ativa da carteira no ciclo; não repete o que já foi gerado."""
    if recorrencias is None:
        recorrencias = db.scalars(
            select(Recorrencia).where(
                Recorrencia.usuario_id == usuario_id,
                Recorrencia.ativa,
                Recorrencia.carteira == carteira,
            )
        ).all()
    for recorrencia in recorrencias:
        if not recorrencia.ativa or recorrencia.carteira != carteira:
            continue
        no_ciclo = [Lancamento.recorrencia_id == recorrencia.id, Lancamento.data >= ciclo.inicio]
        if ciclo.fim is not None:
            no_ciclo.append(Lancamento.data <= ciclo.fim)
        if db.scalar(select(exists().where(*no_ciclo))):
            continue
        db.add(
            Lancamento(
                usuario_id=usuario_id,
                categoria_id=recorrencia.categoria_id,
                data=data_prevista(recorrencia.dia, ciclo.inicio),
                valor=recorrencia.valor,
                tipo=recorrencia.tipo,
                descricao=recorrencia.descricao,
                status=STATUS_PREVISTO,
                recorrencia_id=recorrencia.id,
                carteira=recorrencia.carteira,
                criado_em=agora,
                atualizado_em=agora,
            )
        )


def garantir_previstos_do_mes(
    db: Session, usuario_id: int, hoje: date, agora: datetime, carteira: Carteira = CARTEIRA_PADRAO
) -> None:
    """No ciclo pelo mês (PJ e prestador), nenhum lançamento abre o mês: os previstos do mês
    atual são gerados quando o usuário o consulta. Idempotente; não faz nada no ciclo pelo
    salário."""
    if not ciclo_pelo_mes(tipo_renda_do_usuario(db, usuario_id), carteira):
        return
    travar_escritas(db, usuario_id)
    gerar_previstos(db, usuario_id, ciclo_mensal(hoje, hoje, None), agora, carteira=carteira)
    db.commit()


def criar_recorrencia(
    db: Session, usuario_id: int, dados: RecorrenciaIn, agora: datetime, hoje: date
) -> Recorrencia:
    travar_escritas(db, usuario_id)
    exigir_carteira(db, usuario_id, dados.carteira)
    categoria = _categoria_de_recorrencia(db, usuario_id, dados.categoria_id)
    recorrencia = Recorrencia(
        usuario_id=usuario_id,
        categoria_id=categoria.id,
        descricao=dados.descricao,
        valor=dados.valor,
        tipo=categoria.tipo,
        dia=dados.dia,
        carteira=dados.carteira,
        criado_em=agora,
    )
    db.add(recorrencia)
    db.flush()
    # Com ciclo aberto, o previsto deste ciclo já aparece.
    ciclo = ciclo_atual_do_usuario(db, usuario_id, hoje, dados.carteira)
    if ciclo is not None:
        gerar_previstos(db, usuario_id, ciclo, agora, [recorrencia], carteira=dados.carteira)
    registrar(db, usuario_id, "recorrencia_criada")
    db.commit()
    return recorrencia


def editar_recorrencia(
    db: Session, usuario_id: int, recorrencia_id: int, dados: RecorrenciaPatch
) -> Recorrencia:
    """Muda só a recorrência; lançamentos já gerados ficam como estão."""
    recorrencia = obter_recorrencia(db, usuario_id, recorrencia_id)
    if dados.categoria_id is not None:
        categoria = _categoria_de_recorrencia(db, usuario_id, dados.categoria_id)
        recorrencia.categoria_id = categoria.id
        recorrencia.tipo = categoria.tipo
    if dados.descricao is not None:
        recorrencia.descricao = dados.descricao
    if dados.valor is not None:
        recorrencia.valor = dados.valor
    if dados.dia is not None:
        recorrencia.dia = dados.dia
    if dados.ativa is not None:
        recorrencia.ativa = dados.ativa
    registrar(db, usuario_id, "recorrencia_editada")
    db.commit()
    return recorrencia
