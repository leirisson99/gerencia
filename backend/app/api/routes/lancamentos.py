from fastapi import APIRouter

from app.api.deps import AutenticadoDep, Db, RelogioDep
from app.schemas.erro import ErroOut
from app.schemas.lancamento import LancamentoIn, LancamentoOut, LancamentoPatch
from app.services.lancamento import (
    criar_lancamento,
    editar_lancamento,
    excluir_lancamento,
    obter_lancamento,
)

router = APIRouter(prefix="/api/v1/lancamentos", tags=["lancamentos"])

ERROS_ESCRITA: dict[int | str, dict[str, object]] = {
    404: {"model": ErroOut},
    409: {"model": ErroOut},
    422: {"model": ErroOut},
}


@router.post("", status_code=201, responses=ERROS_ESCRITA)
def criar(dados: LancamentoIn, auth: AutenticadoDep, db: Db, relogio: RelogioDep) -> LancamentoOut:
    lancamento = criar_lancamento(
        db, auth.usuario.id, dados, relogio.agora_utc(), relogio.hoje_sp()
    )
    return LancamentoOut.model_validate(lancamento)


@router.get("/{lancamento_id}", responses={404: {"model": ErroOut}})
def obter(lancamento_id: int, auth: AutenticadoDep, db: Db) -> LancamentoOut:
    return LancamentoOut.model_validate(obter_lancamento(db, auth.usuario.id, lancamento_id))


@router.patch("/{lancamento_id}", responses=ERROS_ESCRITA)
def editar(
    lancamento_id: int,
    dados: LancamentoPatch,
    auth: AutenticadoDep,
    db: Db,
    relogio: RelogioDep,
) -> LancamentoOut:
    lancamento = editar_lancamento(
        db, auth.usuario.id, lancamento_id, dados, relogio.agora_utc(), relogio.hoje_sp()
    )
    return LancamentoOut.model_validate(lancamento)


@router.delete(
    "/{lancamento_id}",
    status_code=204,
    responses={404: {"model": ErroOut}, 409: {"model": ErroOut}},
)
def excluir(lancamento_id: int, auth: AutenticadoDep, db: Db) -> None:
    excluir_lancamento(db, auth.usuario.id, lancamento_id)
