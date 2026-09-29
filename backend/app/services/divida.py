from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.parcelas import datas_das_parcelas, dividir, situacao
from app.erros import MENSAGEM_VALIDACAO, ErroApi
from app.models import Divida, Lancamento
from app.models.divida import CARTAO, DEVO
from app.models.lancamento import STATUS_PREVISTO, STATUS_REALIZADO
from app.schemas.divida import DividaIn, DividaOut
from app.schemas.lancamento import LancamentoOut
from app.services.categoria import obter_categoria_ativa
from app.services.ciclo import travar_escritas
from app.services.lancamento import verificar_novos_lancamentos


def _erro_campo(campo: str, mensagem: str) -> ErroApi:
    return ErroApi(422, "validacao", MENSAGEM_VALIDACAO, campos={campo: mensagem})


def criar_divida(db: Session, usuario_id: int, dados: DividaIn, agora: datetime) -> DividaOut:
    """Cria a dívida e todas as parcelas como previstos, numa transação."""
    travar_escritas(db, usuario_id)
    if dados.valor_total < dados.parcelas:
        raise _erro_campo("valor_total", "Cada parcela precisa de pelo menos 1 centavo.")
    if dados.forma_pagamento == CARTAO and dados.direcao != DEVO:
        raise _erro_campo("forma_pagamento", "Cartão só vale para o que você deve.")

    categoria = obter_categoria_ativa(db, usuario_id, dados.categoria_id)
    tipo_esperado = "saida" if dados.direcao == DEVO else "entrada"
    if categoria.e_salario or categoria.tipo != tipo_esperado:
        raise _erro_campo(
            "categoria_id", f"Use uma categoria de {tipo_esperado.replace('saida', 'saída')}."
        )

    valores = dividir(dados.valor_total, dados.parcelas)
    datas = datas_das_parcelas(dados.dia_vencimento, dados.data_inicio, dados.parcelas)
    verificar_novos_lancamentos(db, usuario_id, datas[0])

    divida = Divida(usuario_id=usuario_id, criado_em=agora, **dados.model_dump())
    db.add(divida)
    db.flush()
    # Parcela paga no cartão entra no saldo só pela fatura.
    conta_no_saldo = dados.forma_pagamento != CARTAO
    for numero, (valor, data) in enumerate(zip(valores, datas, strict=True), start=1):
        db.add(
            Lancamento(
                usuario_id=usuario_id,
                categoria_id=categoria.id,
                data=data,
                valor=valor,
                tipo=categoria.tipo,
                descricao=f"{dados.descricao} ({numero}/{dados.parcelas})",
                status=STATUS_PREVISTO,
                conta_no_saldo=conta_no_saldo,
                divida_id=divida.id,
                parcela_num=numero,
                criado_em=agora,
                atualizado_em=agora,
            )
        )
    db.commit()
    return _saida(db, divida)


def _saida(db: Session, divida: Divida) -> DividaOut:
    parcelas = list(
        db.scalars(
            select(Lancamento)
            .where(Lancamento.divida_id == divida.id)
            .order_by(Lancamento.parcela_num)
        )
    )
    atual = situacao((p.valor, p.status == STATUS_REALIZADO) for p in parcelas)
    return DividaOut(
        id=divida.id,
        descricao=divida.descricao,
        pessoa=divida.pessoa,
        direcao=divida.direcao,
        valor_total=divida.valor_total,
        parcelas=divida.parcelas,
        forma_pagamento=divida.forma_pagamento,
        dia_vencimento=divida.dia_vencimento,
        data_inicio=divida.data_inicio,
        categoria_id=divida.categoria_id,
        parcelas_pagas=atual.pagas,
        valor_pago=atual.valor_pago,
        valor_restante=atual.valor_restante,
        quitada=atual.quitada,
        lancamentos=[LancamentoOut.model_validate(p) for p in parcelas],
    )


def listar_dividas(db: Session, usuario_id: int) -> list[DividaOut]:
    dividas = db.scalars(select(Divida).where(Divida.usuario_id == usuario_id).order_by(Divida.id))
    return [_saida(db, divida) for divida in dividas]


def obter_divida(db: Session, usuario_id: int, divida_id: int) -> DividaOut:
    divida = db.scalar(
        select(Divida).where(Divida.id == divida_id, Divida.usuario_id == usuario_id)
    )
    if divida is None:
        raise ErroApi(404, "nao_encontrado", "Dívida não encontrada.")
    return _saida(db, divida)
