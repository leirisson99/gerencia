from fastapi import APIRouter, Response

from app.api.deps import AutenticadoDep, Db, RelogioDep
from app.schemas.conta_compartilhada import (
    AceiteIn,
    ContaDonoOut,
    ContaIn,
    ContaParticipanteOut,
    ContaPatch,
    ContaResumoOut,
    ConviteIn,
    ConviteOut,
    ParticipantePatch,
)
from app.schemas.erro import ErroOut
from app.services import conta_compartilhada as servico

# Rotas estáticas (/convites, /cotas/...) SEMPRE antes das rotas com /{conta_id}: o FastAPI casa
# na ordem de declaração e tentaria converter "convites" em int.
router = APIRouter(prefix="/api/v1/contas-compartilhadas", tags=["contas-compartilhadas"])

_ERROS = {403: {"model": ErroOut}, 404: {"model": ErroOut}, 409: {"model": ErroOut}}


@router.get("")
def listar(auth: AutenticadoDep, db: Db, relogio: RelogioDep) -> list[ContaResumoOut]:
    return servico.listar_contas(db, auth.usuario.id, relogio.hoje_sp(), relogio.agora_utc())


@router.post(
    "",
    status_code=201,
    responses={404: {"model": ErroOut}, 422: {"model": ErroOut}},
)
def criar(dados: ContaIn, auth: AutenticadoDep, db: Db, relogio: RelogioDep) -> ContaDonoOut:
    return servico.criar_conta(db, auth.usuario.id, dados, relogio.hoje_sp(), relogio.agora_utc())


@router.get("/convites")
def listar_convites(auth: AutenticadoDep, db: Db, relogio: RelogioDep) -> list[ConviteOut]:
    return servico.convites_do_usuario(db, auth.usuario.id, relogio.agora_utc())


@router.post(
    "/convites/{convite_id}/aceitar",
    responses={404: {"model": ErroOut}, 409: {"model": ErroOut}, 422: {"model": ErroOut}},
)
def aceitar_convite(
    convite_id: int, dados: AceiteIn, auth: AutenticadoDep, db: Db, relogio: RelogioDep
) -> ContaParticipanteOut:
    return servico.aceitar_convite(
        db, auth.usuario.id, convite_id, dados, relogio.hoje_sp(), relogio.agora_utc()
    )


@router.post("/convites/{convite_id}/recusar", status_code=204, responses={404: {"model": ErroOut}})
def recusar_convite(convite_id: int, auth: AutenticadoDep, db: Db) -> Response:
    servico.recusar_convite(db, auth.usuario.id, convite_id)
    return Response(status_code=204)


@router.get("/{conta_id}", responses=_ERROS)
def obter(
    conta_id: int, auth: AutenticadoDep, db: Db, relogio: RelogioDep
) -> ContaDonoOut | ContaParticipanteOut:
    return servico.detalhe_da_conta(
        db, conta_id, auth.usuario.id, relogio.hoje_sp(), relogio.agora_utc()
    )


@router.patch("/{conta_id}", responses=_ERROS)
def editar(
    conta_id: int, dados: ContaPatch, auth: AutenticadoDep, db: Db, relogio: RelogioDep
) -> ContaDonoOut:
    return servico.editar_conta(
        db, auth.usuario.id, conta_id, dados, relogio.hoje_sp(), relogio.agora_utc()
    )


@router.post("/{conta_id}/participantes", status_code=201, responses=_ERROS)
def convidar(
    conta_id: int, dados: ConviteIn, auth: AutenticadoDep, db: Db, relogio: RelogioDep
) -> ContaDonoOut:
    return servico.convidar(
        db, auth.usuario.id, conta_id, dados, relogio.hoje_sp(), relogio.agora_utc()
    )


@router.patch("/{conta_id}/participantes/{participante_id}", responses=_ERROS)
def editar_valor(
    conta_id: int,
    participante_id: int,
    dados: ParticipantePatch,
    auth: AutenticadoDep,
    db: Db,
    relogio: RelogioDep,
) -> ContaDonoOut:
    return servico.editar_valor_participante(
        db,
        auth.usuario.id,
        conta_id,
        participante_id,
        dados,
        relogio.hoje_sp(),
        relogio.agora_utc(),
    )


@router.delete("/{conta_id}/participantes/{participante_id}", responses=_ERROS)
def remover(
    conta_id: int, participante_id: int, auth: AutenticadoDep, db: Db, relogio: RelogioDep
) -> ContaDonoOut:
    return servico.remover_participante(
        db, auth.usuario.id, conta_id, participante_id, relogio.hoje_sp(), relogio.agora_utc()
    )


@router.post("/{conta_id}/sair", status_code=204, responses=_ERROS)
def sair(conta_id: int, auth: AutenticadoDep, db: Db) -> Response:
    servico.sair_da_conta(db, auth.usuario.id, conta_id)
    return Response(status_code=204)
