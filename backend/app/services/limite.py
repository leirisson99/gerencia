"""Uso do limite de uma categoria num ciclo e o aviso quando a situação piora."""

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.limite import piorou, situacao
from app.domain.saldo import Movimento, resumir
from app.domain.usuario import CARTEIRA_PADRAO, Carteira
from app.models import Categoria, Lancamento
from app.schemas.lancamento import AvisoLimiteOut
from app.services.ciclo import ciclo_da_data_do_usuario


def usado_no_ciclo(
    db: Session,
    usuario_id: int,
    categoria: Categoria,
    data: date,
    hoje: date,
    carteira: Carteira = CARTEIRA_PADRAO,
) -> int | None:
    """Gasto que conta no saldo, na categoria, no ciclo da data, só na carteira.

    `None` se não há o que medir.
    """
    if categoria.limite is None or categoria.tipo != "saida":
        return None
    ciclo = ciclo_da_data_do_usuario(db, usuario_id, data, hoje, carteira)
    if ciclo is None:
        return None
    consulta = select(Lancamento).where(
        Lancamento.usuario_id == usuario_id,
        Lancamento.categoria_id == categoria.id,
        Lancamento.carteira == carteira,
        Lancamento.data >= ciclo.inicio,
    )
    if ciclo.fim is not None:
        consulta = consulta.where(Lancamento.data <= ciclo.fim)
    resumo = resumir(
        Movimento(lanc.categoria_id, lanc.tipo, lanc.valor, lanc.status, lanc.conta_no_saldo)
        for lanc in db.scalars(consulta)
    )
    return resumo.por_categoria.get(categoria.id, 0)


def avaliar_aviso(
    categoria: Categoria, antes: int | None, depois: int | None
) -> AvisoLimiteOut | None:
    """Aviso só quando a situação sobe de nível (ok → atenção → estourado)."""
    if categoria.limite is None or antes is None or depois is None:
        return None
    nova = situacao(depois, categoria.limite)
    if not piorou(situacao(antes, categoria.limite), nova):
        return None
    return AvisoLimiteOut(
        categoria_id=categoria.id,
        nome=categoria.nome,
        usado=depois,
        limite=categoria.limite,
        situacao=nova,
    )
