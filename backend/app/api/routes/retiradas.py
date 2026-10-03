from fastapi import APIRouter

from app.api.deps import AutenticadoDep, Db, RelogioDep
from app.schemas.erro import ErroOut
from app.schemas.retirada import RetiradaIn, RetiradaOut, RetiradaPatch
from app.services.retirada import (
    criar_retirada,
    editar_retirada,
    excluir_retirada,
    listar_retiradas,
    obter_retirada,
)

router = APIRouter(prefix="/api/v1/retiradas", tags=["retiradas"])

ERROS: dict[int | str, dict[str, object]] = {
    404: {"model": ErroOut},
    409: {"model": ErroOut},
    422: {"model": ErroOut},
}


@router.get("", responses={409: {"model": ErroOut}})
def listar(auth: AutenticadoDep, db: Db) -> list[RetiradaOut]:
    return [RetiradaOut.model_validate(r) for r in listar_retiradas(db, auth.usuario.id)]


@router.post("", status_code=201, responses=ERROS)
def criar(dados: RetiradaIn, auth: AutenticadoDep, db: Db, relogio: RelogioDep) -> RetiradaOut:
    retirada = criar_retirada(db, auth.usuario.id, dados, relogio.agora_utc(), relogio.hoje_sp())
    return RetiradaOut.model_validate(retirada)


@router.get("/{retirada_id}", responses=ERROS)
def obter(retirada_id: int, auth: AutenticadoDep, db: Db) -> RetiradaOut:
    return RetiradaOut.model_validate(obter_retirada(db, auth.usuario.id, retirada_id))


@router.patch("/{retirada_id}", responses=ERROS)
def editar(
    retirada_id: int, dados: RetiradaPatch, auth: AutenticadoDep, db: Db, relogio: RelogioDep
) -> RetiradaOut:
    retirada = editar_retirada(
        db, auth.usuario.id, retirada_id, dados, relogio.agora_utc(), relogio.hoje_sp()
    )
    return RetiradaOut.model_validate(retirada)


@router.delete("/{retirada_id}", status_code=204, responses=ERROS)
def excluir(retirada_id: int, auth: AutenticadoDep, db: Db) -> None:
    excluir_retirada(db, auth.usuario.id, retirada_id)
