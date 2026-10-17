from fastapi import APIRouter

from app.api.deps import AutenticadoDep, Db, RelogioDep
from app.schemas.conta_compartilhada import (
    ContaDonoOut,
    ContaIn,
    ContaPatch,
    ContaResumoOut,
    ConviteIn,
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


@router.get("/{conta_id}", responses=_ERROS)
def obter(conta_id: int, auth: AutenticadoDep, db: Db, relogio: RelogioDep) -> ContaDonoOut:
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
