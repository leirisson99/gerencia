"""Contas compartilhadas entre usuários (constituição 8.1.0, princípios I e V).

Acesso: só o dono e os participantes `aceito` enxergam uma conta; qualquer outro recebe 404.
Todo acesso passa por `conta_visivel` ou `conta_do_dono`.
"""

from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.conta_compartilhada import (
    MAX_PARTICIPANTES,
    TOTAL_BPS,
    convite_expirado,
    status_da_cota,
)
from app.erros import MENSAGEM_VALIDACAO, ErroApi
from app.models import (
    Categoria,
    CobrancaMensal,
    ContaCompartilhada,
    CotaCobranca,
    Lancamento,
    ParticipanteConta,
    Usuario,
)
from app.models.conta_compartilhada import ACEITO, PENDENTE, RECUSADO, REMOVIDO, SAIU
from app.schemas.conta_compartilhada import (
    ContaDonoOut,
    ContaIn,
    ContaPatch,
    ContaResumoOut,
    ConviteIn,
    MinhaCotaOut,
    ParticipanteDonoOut,
    ParticipantePatch,
)
from app.services.categoria import obter_categoria_ativa
from app.services.evento_uso import registrar


def _nao_encontrada() -> ErroApi:
    return ErroApi(404, "nao_encontrado", "Conta não encontrada.")


def conta_visivel(
    db: Session, conta_id: int, usuario_id: int
) -> tuple[ContaCompartilhada, ParticipanteConta]:
    """A conta e a participação do usuário nela; 404 se não for dono nem participante aceito."""
    linha = db.execute(
        select(ContaCompartilhada, ParticipanteConta)
        .join(ParticipanteConta, ParticipanteConta.conta_id == ContaCompartilhada.id)
        .where(
            ContaCompartilhada.id == conta_id,
            ParticipanteConta.usuario_id == usuario_id,
            ParticipanteConta.status == ACEITO,
        )
    ).first()
    if linha is None:
        raise _nao_encontrada()
    return linha[0], linha[1]


def conta_do_dono(db: Session, conta_id: int, usuario_id: int) -> ContaCompartilhada:
    """Só o dono edita: 404 para quem não participa, 403 para participante aceito."""
    conta, participacao = conta_visivel(db, conta_id, usuario_id)
    if not participacao.eh_dono:
        raise ErroApi(403, "somente_dono", "Só o dono da conta pode fazer isso.")
    return conta


# --- leitura ---------------------------------------------------------------------------------


def _competencia(hoje: date) -> date:
    return date(hoje.year, hoje.month, 1)


def _pendente_valido(participante: ParticipanteConta, agora: datetime) -> bool:
    return participante.status == PENDENTE and not convite_expirado(
        participante.convidado_em, agora
    )


def _participantes(db: Session, conta_id: int) -> list[ParticipanteConta]:
    return list(
        db.scalars(
            select(ParticipanteConta)
            .where(ParticipanteConta.conta_id == conta_id)
            .order_by(ParticipanteConta.id)
        )
    )


def _cobranca_do_mes(db: Session, conta_id: int, competencia: date) -> CobrancaMensal | None:
    return db.scalar(
        select(CobrancaMensal).where(
            CobrancaMensal.conta_id == conta_id, CobrancaMensal.competencia == competencia
        )
    )


def _cotas_da_cobranca(
    db: Session, cobranca: CobrancaMensal | None
) -> dict[int, tuple[CotaCobranca, str | None]]:
    """Cota de cada participante e o status do lançamento dela (nulo se ainda não existe)."""
    if cobranca is None:
        return {}
    linhas = db.execute(
        select(CotaCobranca, Lancamento.status)
        .outerjoin(Lancamento, Lancamento.id == CotaCobranca.lancamento_id)
        .where(CotaCobranca.cobranca_id == cobranca.id)
    )
    return {cota.participante_id: (cota, status) for cota, status in linhas}


def _minha_cota(
    participacao: ParticipanteConta, cotas: dict[int, tuple[CotaCobranca, str | None]]
) -> MinhaCotaOut | None:
    achado = cotas.get(participacao.id)
    if achado is None:
        return None
    cota, status_lancamento = achado
    return MinhaCotaOut(
        id=cota.id,
        valor=cota.valor,
        status=status_da_cota(status_lancamento, cota.confirmado_em),
        lancamento_id=cota.lancamento_id,
    )


def _contagens(participantes: list[ParticipanteConta], agora: datetime) -> tuple[int, int]:
    aceitos = sum(1 for p in participantes if p.status == ACEITO)
    pendentes = sum(1 for p in participantes if _pendente_valido(p, agora))
    return aceitos, pendentes


def _nome_dos_usuarios(db: Session, participantes: list[ParticipanteConta]) -> dict[int, str]:
    ids = {p.usuario_id for p in participantes if p.usuario_id is not None}
    if not ids:
        return {}
    return dict(db.execute(select(Usuario.id, Usuario.nome).where(Usuario.id.in_(ids))).all())


def _visao_do_dono(
    db: Session,
    conta: ContaCompartilhada,
    participacao: ParticipanteConta,
    hoje: date,
    agora: datetime,
) -> ContaDonoOut:
    participantes = _participantes(db, conta.id)
    cobranca = _cobranca_do_mes(db, conta.id, _competencia(hoje))
    cotas = _cotas_da_cobranca(db, cobranca)
    nomes = _nome_dos_usuarios(db, participantes)
    aceitos, pendentes = _contagens(participantes, agora)
    linhas = []
    for p in participantes:
        achado = cotas.get(p.id)
        minha = _minha_cota(p, cotas)
        linhas.append(
            ParticipanteDonoOut(
                id=p.id,
                # O nome só aparece depois do aceite: antes disso o dono só sabe o e-mail.
                nome=nomes.get(p.usuario_id) if p.status == ACEITO and p.usuario_id else None,
                email_convite=p.email_convite,
                status=p.status,
                expirado=p.status == PENDENTE and convite_expirado(p.convidado_em, agora),
                eh_dono=p.eh_dono,
                valor=p.valor,
                cota_id=achado[0].id if achado else None,
                cota=achado[0].valor if achado else None,
                status_cota=minha.status if minha else None,
            )
        )
    return ContaDonoOut(
        id=conta.id,
        descricao=conta.descricao,
        categoria_id=conta.categoria_id,
        modo=conta.modo,
        dia_vencimento=conta.dia_vencimento,
        valor_fixo=conta.valor_fixo,
        ativa=conta.ativa,
        valor_total=cobranca.valor_total if cobranca else None,
        qtd_pessoas=aceitos,
        qtd_convidados_pendentes=pendentes,
        falta_informar_total=conta.ativa and conta.valor_fixo is None and cobranca is None,
        minha_cota=_minha_cota(participacao, cotas),
        participantes=linhas,
    )


def detalhe_da_conta(
    db: Session, conta_id: int, usuario_id: int, hoje: date, agora: datetime
) -> ContaDonoOut:
    conta, participacao = conta_visivel(db, conta_id, usuario_id)
    # A visão do participante entra na US2; até lá só o dono é aceito numa conta.
    assert participacao.eh_dono, "participante aceito só existe depois do aceite de convite"
    return _visao_do_dono(db, conta, participacao, hoje, agora)


def listar_contas(
    db: Session, usuario_id: int, hoje: date, agora: datetime
) -> list[ContaResumoOut]:
    linhas = db.execute(
        select(ContaCompartilhada, ParticipanteConta)
        .join(ParticipanteConta, ParticipanteConta.conta_id == ContaCompartilhada.id)
        .where(ParticipanteConta.usuario_id == usuario_id, ParticipanteConta.status == ACEITO)
        .order_by(ContaCompartilhada.id.desc())
    ).all()
    resumos = []
    for conta, participacao in linhas:
        participantes = _participantes(db, conta.id)
        cobranca = _cobranca_do_mes(db, conta.id, _competencia(hoje))
        aceitos, pendentes = _contagens(participantes, agora)
        resumos.append(
            ContaResumoOut(
                id=conta.id,
                descricao=conta.descricao,
                papel="dono" if participacao.eh_dono else "participante",
                ativa=conta.ativa,
                dia_vencimento=conta.dia_vencimento,
                valor_total=cobranca.valor_total if cobranca else None,
                qtd_pessoas=aceitos,
                qtd_convidados_pendentes=pendentes,
                minha_cota=_minha_cota(participacao, _cotas_da_cobranca(db, cobranca)),
                falta_informar_total=participacao.eh_dono
                and conta.ativa
                and conta.valor_fixo is None
                and cobranca is None,
            )
        )
    return resumos


# --- escrita do dono ---------------------------------------------------------------------------


def _categoria_de_saida(db: Session, usuario_id: int, categoria_id: int) -> Categoria:
    categoria = obter_categoria_ativa(db, usuario_id, categoria_id)
    if categoria.tipo != "saida":
        raise ErroApi(
            422,
            "validacao",
            MENSAGEM_VALIDACAO,
            campos={"categoria_id": "Use uma categoria de saída."},
        )
    return categoria


def _validar_valor_da_parte(modo: str, valor: int | None) -> None:
    if modo == "percentual" and valor is not None and valor > TOTAL_BPS:
        raise ErroApi(422, "validacao", MENSAGEM_VALIDACAO, campos={"valor": "O máximo é 100%."})


def _travar_conta(db: Session, conta_id: int) -> ContaCompartilhada:
    conta = db.scalar(
        select(ContaCompartilhada).where(ContaCompartilhada.id == conta_id).with_for_update()
    )
    assert conta is not None, "a conta foi lida logo antes"
    return conta


def criar_conta(
    db: Session, usuario_id: int, dados: ContaIn, hoje: date, agora: datetime
) -> ContaDonoOut:
    categoria = _categoria_de_saida(db, usuario_id, dados.categoria_id)
    conta = ContaCompartilhada(
        dono_id=usuario_id,
        categoria_id=categoria.id,
        descricao=dados.descricao,
        modo=dados.modo,
        dia_vencimento=dados.dia_vencimento,
        valor_fixo=dados.valor_fixo,
        criado_em=agora,
    )
    db.add(conta)
    db.flush()
    dono = ParticipanteConta(
        conta_id=conta.id,
        usuario_id=usuario_id,
        status=ACEITO,
        categoria_id=categoria.id,
        eh_dono=True,
        convidado_em=agora,
    )
    db.add(dono)
    registrar(db, usuario_id, "conta_compartilhada_criada")
    db.commit()
    return _visao_do_dono(db, conta, dono, hoje, agora)


def editar_conta(
    db: Session, usuario_id: int, conta_id: int, dados: ContaPatch, hoje: date, agora: datetime
) -> ContaDonoOut:
    conta = conta_do_dono(db, conta_id, usuario_id)
    conta = _travar_conta(db, conta.id)
    enviados = dados.model_fields_set
    if dados.descricao is not None:
        conta.descricao = dados.descricao
    if dados.dia_vencimento is not None:
        conta.dia_vencimento = dados.dia_vencimento
    if dados.modo is not None:
        conta.modo = dados.modo
    if "valor_fixo" in enviados:
        conta.valor_fixo = dados.valor_fixo
    if dados.ativa is not None:
        conta.ativa = dados.ativa
    if dados.categoria_id is not None:
        categoria = _categoria_de_saida(db, usuario_id, dados.categoria_id)
        conta.categoria_id = categoria.id
        # A cota do dono cai na categoria da conta.
        dono = _participante_do_dono(db, conta.id)
        dono.categoria_id = categoria.id
    db.commit()
    return detalhe_da_conta(db, conta.id, usuario_id, hoje, agora)


def _participante_do_dono(db: Session, conta_id: int) -> ParticipanteConta:
    dono = db.scalar(
        select(ParticipanteConta).where(
            ParticipanteConta.conta_id == conta_id, ParticipanteConta.eh_dono
        )
    )
    assert dono is not None, "toda conta nasce com o participante dono"
    return dono


def convidar(
    db: Session,
    usuario_id: int,
    conta_id: int,
    dados: ConviteIn,
    hoje: date,
    agora: datetime,
) -> ContaDonoOut:
    """Convida por e-mail. A resposta é a mesma exista conta para o e-mail ou não, e um convite
    repetido não duplica: o dono não descobre quem tem conta no app."""
    conta = conta_do_dono(db, conta_id, usuario_id)
    conta = _travar_conta(db, conta.id)
    _validar_valor_da_parte(conta.modo, dados.valor)
    dono = db.get(Usuario, usuario_id)
    assert dono is not None
    participantes = _participantes(db, conta.id)
    existente = next((p for p in participantes if p.email_convite == dados.email), None)
    if dados.email != dono.email:
        reabrir = existente is not None and (
            existente.status in (RECUSADO, REMOVIDO, SAIU)
            or (existente.status == PENDENTE and convite_expirado(existente.convidado_em, agora))
        )
        if existente is None or reabrir:
            ativos = sum(
                1 for p in participantes if p.status == ACEITO or _pendente_valido(p, agora)
            )
            if ativos >= MAX_PARTICIPANTES:
                raise ErroApi(
                    409,
                    "limite_participantes",
                    f"Uma conta tem no máximo {MAX_PARTICIPANTES} participantes.",
                )
        if existente is None:
            db.add(
                ParticipanteConta(
                    conta_id=conta.id,
                    email_convite=dados.email,
                    status=PENDENTE,
                    valor=dados.valor,
                    convidado_em=agora,
                )
            )
        elif reabrir:
            existente.status = PENDENTE
            existente.convidado_em = agora
            existente.usuario_id = None
            existente.categoria_id = None
            if dados.valor is not None:
                existente.valor = dados.valor
        elif dados.valor is not None:
            existente.valor = dados.valor
    db.commit()
    return detalhe_da_conta(db, conta.id, usuario_id, hoje, agora)


def _participante_da_conta(db: Session, conta_id: int, participante_id: int) -> ParticipanteConta:
    participante = db.scalar(
        select(ParticipanteConta).where(
            ParticipanteConta.id == participante_id, ParticipanteConta.conta_id == conta_id
        )
    )
    if participante is None:
        raise ErroApi(404, "nao_encontrado", "Participante não encontrado.")
    return participante


def editar_valor_participante(
    db: Session,
    usuario_id: int,
    conta_id: int,
    participante_id: int,
    dados: ParticipantePatch,
    hoje: date,
    agora: datetime,
) -> ContaDonoOut:
    conta = conta_do_dono(db, conta_id, usuario_id)
    _validar_valor_da_parte(conta.modo, dados.valor)
    participante = _participante_da_conta(db, conta.id, participante_id)
    if participante.status in (RECUSADO, REMOVIDO, SAIU):
        raise ErroApi(404, "nao_encontrado", "Participante não encontrado.")
    participante.valor = dados.valor
    db.commit()
    return detalhe_da_conta(db, conta.id, usuario_id, hoje, agora)


def remover_participante(
    db: Session, usuario_id: int, conta_id: int, participante_id: int, hoje: date, agora: datetime
) -> ContaDonoOut:
    """Vale da próxima cobrança: as cotas já geradas ficam como estão."""
    conta = conta_do_dono(db, conta_id, usuario_id)
    participante = _participante_da_conta(db, conta.id, participante_id)
    if participante.eh_dono:
        raise ErroApi(409, "dono_nao_removivel", "O dono não pode ser removido da conta.")
    participante.status = REMOVIDO
    db.commit()
    return detalhe_da_conta(db, conta.id, usuario_id, hoje, agora)
