"""Retirada da PJ para a PF: a retirada é dona dos dois lançamentos e os muda sempre juntos."""

from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.categoria import NOME_PRO_LABORE, NOME_RETIRADA_PJ
from app.domain.retirada import lados_da_retirada, validar_retirada
from app.erros import MENSAGEM_VALIDACAO, ErroApi
from app.models import Categoria, Lancamento, Retirada
from app.models.lancamento import STATUS_REALIZADO
from app.schemas.retirada import RetiradaIn, RetiradaPatch
from app.services.ciclo import exigir_carteira, travar_escritas
from app.services.evento_uso import registrar
from app.services.lancamento import _problema_depois_da_mudanca, erro_de_cobertura


def _validar(valor: int, data: date, hoje: date) -> None:
    erros = validar_retirada(valor, data, hoje)
    if erros:
        raise ErroApi(422, "validacao", MENSAGEM_VALIDACAO, campos=erros)


def _verificar_lado_pf(db: Session, usuario_id: int, data: date, ignorar_id: int | None) -> None:
    """O lado PF é uma entrada como outra: precisa cair num ciclo da PF."""
    resultado = _problema_depois_da_mudanca(db, usuario_id, ignorar_id, (False, data))
    if resultado:
        raise erro_de_cobertura(*resultado)


def _categoria_de_sistema(db: Session, usuario_id: int, nome: str) -> Categoria:
    categoria = db.scalar(
        select(Categoria).where(
            Categoria.usuario_id == usuario_id, Categoria.sistema, Categoria.nome == nome
        )
    )
    assert categoria is not None, "criada ao ligar a PJ"
    return categoria


def _lados(db: Session, retirada: Retirada) -> tuple[Lancamento, Lancamento]:
    pj = db.get(Lancamento, retirada.lancamento_pj_id)
    pf = db.get(Lancamento, retirada.lancamento_pf_id)
    assert pj is not None and pf is not None
    return pj, pf


def listar_retiradas(db: Session, usuario_id: int) -> list[Retirada]:
    exigir_carteira(db, usuario_id, "pj")
    return list(
        db.scalars(
            select(Retirada)
            .where(Retirada.usuario_id == usuario_id)
            .order_by(Retirada.data.desc(), Retirada.id.desc())
        )
    )


def obter_retirada(db: Session, usuario_id: int, retirada_id: int) -> Retirada:
    exigir_carteira(db, usuario_id, "pj")
    retirada = db.scalar(
        select(Retirada).where(Retirada.id == retirada_id, Retirada.usuario_id == usuario_id)
    )
    if retirada is None:
        raise ErroApi(404, "nao_encontrado", "Retirada não encontrada.")
    return retirada


def criar_retirada(
    db: Session, usuario_id: int, dados: RetiradaIn, agora: datetime, hoje: date
) -> Retirada:
    travar_escritas(db, usuario_id)
    exigir_carteira(db, usuario_id, "pj")
    _validar(dados.valor, dados.data, hoje)
    _verificar_lado_pf(db, usuario_id, dados.data, None)

    categorias = {
        "pj": _categoria_de_sistema(db, usuario_id, NOME_RETIRADA_PJ),
        "pf": _categoria_de_sistema(db, usuario_id, NOME_PRO_LABORE),
    }
    lancamentos = {}
    for lado in lados_da_retirada(dados.valor, dados.data):
        lancamento = Lancamento(
            usuario_id=usuario_id,
            categoria_id=categorias[lado.carteira].id,
            data=lado.data,
            valor=lado.valor,
            tipo=lado.tipo,
            descricao=dados.descricao,
            status=STATUS_REALIZADO,
            carteira=lado.carteira,
            criado_em=agora,
            atualizado_em=agora,
        )
        db.add(lancamento)
        lancamentos[lado.carteira] = lancamento
    db.flush()

    retirada = Retirada(
        usuario_id=usuario_id,
        data=dados.data,
        valor=dados.valor,
        descricao=dados.descricao,
        lancamento_pj_id=lancamentos["pj"].id,
        lancamento_pf_id=lancamentos["pf"].id,
        criado_em=agora,
    )
    db.add(retirada)
    registrar(db, usuario_id, "retirada_feita")
    db.commit()
    return retirada


def editar_retirada(
    db: Session,
    usuario_id: int,
    retirada_id: int,
    dados: RetiradaPatch,
    agora: datetime,
    hoje: date,
) -> Retirada:
    travar_escritas(db, usuario_id)
    retirada = obter_retirada(db, usuario_id, retirada_id)
    enviados = dados.model_fields_set
    if not enviados:
        return retirada
    valor = dados.valor if dados.valor is not None else retirada.valor
    data = dados.data if dados.data is not None else retirada.data
    _validar(valor, data, hoje)
    if data != retirada.data:
        _verificar_lado_pf(db, usuario_id, data, retirada.lancamento_pf_id)

    retirada.valor = valor
    retirada.data = data
    if "descricao" in enviados:
        retirada.descricao = dados.descricao
    for lado in _lados(db, retirada):
        lado.valor = valor
        lado.data = data
        lado.descricao = retirada.descricao
        lado.atualizado_em = agora
    registrar(db, usuario_id, "retirada_editada")
    db.commit()
    return retirada


def excluir_retirada(db: Session, usuario_id: int, retirada_id: int) -> None:
    """Apagar uma entrada da PF nunca deixa outro lançamento fora de ciclo."""
    travar_escritas(db, usuario_id)
    retirada = obter_retirada(db, usuario_id, retirada_id)
    lados = _lados(db, retirada)
    db.delete(retirada)
    db.flush()
    for lado in lados:
        db.delete(lado)
    registrar(db, usuario_id, "retirada_excluida")
    db.commit()
