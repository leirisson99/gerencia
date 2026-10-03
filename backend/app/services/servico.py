from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.servico import SituacaoServico, descricao_do_lancamento, situacao
from app.erros import MENSAGEM_VALIDACAO, ErroApi
from app.models import Categoria, Lancamento, Servico
from app.models.lancamento import STATUS_PREVISTO, STATUS_REALIZADO
from app.schemas.servico import RecebimentoIn, ServicoIn, ServicoOut, ServicoPatch
from app.services.categoria import obter_categoria_ativa
from app.services.ciclo import travar_escritas
from app.services.evento_uso import registrar
from app.services.lancamento import verificar_novos_lancamentos


def _erro_campo(campo: str, mensagem: str) -> ErroApi:
    return ErroApi(422, "validacao", MENSAGEM_VALIDACAO, campos={campo: mensagem})


def _categoria_de_servico(db: Session, usuario_id: int, categoria_id: int) -> Categoria:
    categoria = obter_categoria_ativa(db, usuario_id, categoria_id)
    if categoria.tipo != "entrada" or categoria.e_salario:
        raise _erro_campo("categoria_id", "Use uma categoria de entrada que não seja Salário.")
    return categoria


def _obter(db: Session, usuario_id: int, servico_id: int) -> tuple[Servico, Lancamento]:
    linha = db.execute(
        select(Servico, Lancamento)
        .join(Lancamento, Servico.lancamento_id == Lancamento.id)
        .where(Servico.id == servico_id, Servico.usuario_id == usuario_id)
    ).one_or_none()
    if linha is None:
        raise ErroApi(404, "nao_encontrado", "Serviço não encontrado.")
    servico, lancamento = linha
    return servico, lancamento


def _recebido(lancamento: Lancamento) -> bool:
    return lancamento.status == STATUS_REALIZADO


def _exigir_nao_recebido(lancamento: Lancamento) -> None:
    if _recebido(lancamento):
        raise ErroApi(
            409, "servico_recebido", "O serviço já foi recebido. Desfaça o recebimento antes."
        )


def _saida(servico: Servico, lancamento: Lancamento, hoje: date) -> ServicoOut:
    recebido = _recebido(lancamento)
    return ServicoOut(
        id=servico.id,
        cliente=servico.cliente,
        descricao=servico.descricao,
        valor=servico.valor,
        data_prevista=servico.data_prevista,
        categoria_id=servico.categoria_id,
        lancamento_id=servico.lancamento_id,
        situacao=situacao(lancamento.status, servico.data_prevista, hoje),
        data_recebimento=lancamento.data if recebido else None,
        valor_recebido=lancamento.valor if recebido else None,
        criado_em=servico.criado_em,
    )


def listar_servicos(
    db: Session, usuario_id: int, hoje: date, filtro: SituacaoServico | None
) -> list[ServicoOut]:
    linhas = db.execute(
        select(Servico, Lancamento)
        .join(Lancamento, Servico.lancamento_id == Lancamento.id)
        .where(Servico.usuario_id == usuario_id)
        .order_by(Servico.data_prevista, Servico.id)
    )
    saidas = [_saida(servico, lancamento, hoje) for servico, lancamento in linhas]
    return [s for s in saidas if filtro is None or s.situacao == filtro]


def obter_servico(db: Session, usuario_id: int, servico_id: int, hoje: date) -> ServicoOut:
    return _saida(*_obter(db, usuario_id, servico_id), hoje)


def criar_servico(
    db: Session, usuario_id: int, dados: ServicoIn, agora: datetime, hoje: date
) -> ServicoOut:
    """Grava o serviço e a entrada prevista, numa transação."""
    travar_escritas(db, usuario_id)
    categoria = _categoria_de_servico(db, usuario_id, dados.categoria_id)
    verificar_novos_lancamentos(db, usuario_id, dados.data_prevista)

    lancamento = Lancamento(
        usuario_id=usuario_id,
        categoria_id=categoria.id,
        data=dados.data_prevista,
        valor=dados.valor,
        tipo=categoria.tipo,
        descricao=descricao_do_lancamento(dados.cliente, dados.descricao),
        status=STATUS_PREVISTO,
        criado_em=agora,
        atualizado_em=agora,
    )
    db.add(lancamento)
    db.flush()
    servico = Servico(
        usuario_id=usuario_id,
        categoria_id=categoria.id,
        cliente=dados.cliente,
        descricao=dados.descricao,
        valor=dados.valor,
        data_prevista=dados.data_prevista,
        lancamento_id=lancamento.id,
        criado_em=agora,
    )
    db.add(servico)
    registrar(db, usuario_id, "servico_criado")
    db.commit()
    return _saida(servico, lancamento, hoje)


def editar_servico(
    db: Session,
    usuario_id: int,
    servico_id: int,
    dados: ServicoPatch,
    agora: datetime,
    hoje: date,
) -> ServicoOut:
    """Só enquanto não recebido; a entrada prevista acompanha."""
    travar_escritas(db, usuario_id)
    servico, lancamento = _obter(db, usuario_id, servico_id)
    enviados = dados.model_fields_set
    if not enviados:
        return _saida(servico, lancamento, hoje)
    _exigir_nao_recebido(lancamento)

    if dados.categoria_id is not None and dados.categoria_id != servico.categoria_id:
        categoria = _categoria_de_servico(db, usuario_id, dados.categoria_id)
        servico.categoria_id = lancamento.categoria_id = categoria.id
        lancamento.tipo = categoria.tipo
    if dados.data_prevista is not None and dados.data_prevista != servico.data_prevista:
        verificar_novos_lancamentos(db, usuario_id, dados.data_prevista)
        servico.data_prevista = lancamento.data = dados.data_prevista
    if dados.valor is not None:
        servico.valor = lancamento.valor = dados.valor
    if dados.cliente is not None:
        servico.cliente = dados.cliente
    if "descricao" in enviados:
        servico.descricao = dados.descricao
    lancamento.descricao = descricao_do_lancamento(servico.cliente, servico.descricao)
    lancamento.atualizado_em = agora
    registrar(db, usuario_id, "servico_editado")
    db.commit()
    return _saida(servico, lancamento, hoje)


def excluir_servico(db: Session, usuario_id: int, servico_id: int) -> None:
    travar_escritas(db, usuario_id)
    servico, lancamento = _obter(db, usuario_id, servico_id)
    _exigir_nao_recebido(lancamento)
    db.delete(servico)
    db.flush()  # a entrada só sai depois do serviço que a referencia
    db.delete(lancamento)
    registrar(db, usuario_id, "servico_excluido")
    db.commit()


def receber_servico(
    db: Session,
    usuario_id: int,
    servico_id: int,
    dados: RecebimentoIn,
    agora: datetime,
    hoje: date,
) -> ServicoOut:
    """A entrada vira realizada, com a data e o valor recebidos; o serviço guarda o combinado."""
    travar_escritas(db, usuario_id)
    servico, lancamento = _obter(db, usuario_id, servico_id)
    _exigir_nao_recebido(lancamento)
    if dados.data > hoje:
        raise _erro_campo("data", "O recebimento é marcado quando o dinheiro entra.")
    verificar_novos_lancamentos(db, usuario_id, dados.data)

    lancamento.status = STATUS_REALIZADO
    lancamento.data = dados.data
    lancamento.valor = dados.valor if dados.valor is not None else servico.valor
    lancamento.atualizado_em = agora
    registrar(db, usuario_id, "servico_recebido")
    db.commit()
    return _saida(servico, lancamento, hoje)


def desfazer_recebimento(
    db: Session, usuario_id: int, servico_id: int, agora: datetime, hoje: date
) -> ServicoOut:
    """A entrada volta a prevista, na data prevista e com o valor combinado."""
    travar_escritas(db, usuario_id)
    servico, lancamento = _obter(db, usuario_id, servico_id)
    if not _recebido(lancamento):
        raise ErroApi(409, "servico_nao_recebido", "O serviço ainda não foi recebido.")
    verificar_novos_lancamentos(db, usuario_id, servico.data_prevista)

    lancamento.status = STATUS_PREVISTO
    lancamento.data = servico.data_prevista
    lancamento.valor = servico.valor
    lancamento.atualizado_em = agora
    registrar(db, usuario_id, "recebimento_desfeito")
    db.commit()
    return _saida(servico, lancamento, hoje)
