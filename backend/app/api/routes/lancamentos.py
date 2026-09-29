from fastapi import APIRouter

from app.api.deps import AutenticadoDep, Db, RelogioDep
from app.models import Lancamento
from app.schemas.erro import ErroOut
from app.schemas.lancamento import (
    AvisoLimiteOut,
    LancamentoComAvisoOut,
    LancamentoIn,
    LancamentoOut,
    LancamentoPatch,
)
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


def _com_aviso(lancamento: Lancamento, aviso: AvisoLimiteOut | None) -> LancamentoComAvisoOut:
    return LancamentoComAvisoOut(
        **LancamentoOut.model_validate(lancamento).model_dump(), aviso_limite=aviso
    )


@router.post("", status_code=201, responses=ERROS_ESCRITA)
def criar(
    dados: LancamentoIn, auth: AutenticadoDep, db: Db, relogio: RelogioDep
) -> LancamentoComAvisoOut:
    lancamento, aviso = criar_lancamento(
        db, auth.usuario.id, dados, relogio.agora_utc(), relogio.hoje_sp()
    )
    return _com_aviso(lancamento, aviso)


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
) -> LancamentoComAvisoOut:
    lancamento, aviso = editar_lancamento(
        db, auth.usuario.id, lancamento_id, dados, relogio.agora_utc(), relogio.hoje_sp()
    )
    return _com_aviso(lancamento, aviso)


@router.delete(
    "/{lancamento_id}",
    status_code=204,
    responses={404: {"model": ErroOut}, 409: {"model": ErroOut}},
)
def excluir(lancamento_id: int, auth: AutenticadoDep, db: Db) -> None:
    excluir_lancamento(db, auth.usuario.id, lancamento_id)
