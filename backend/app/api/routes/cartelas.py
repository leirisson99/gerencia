from fastapi import APIRouter

from app.api.deps import AutenticadoDep, Db, RelogioDep
from app.schemas.cartela import CartelaIn, CartelaOut
from app.schemas.erro import ErroOut
from app.services.cartela import (
    criar_cartela,
    depositar,
    desfazer_deposito,
    listar_cartelas,
    obter_cartela,
)

router = APIRouter(prefix="/api/v1/cartelas", tags=["cartelas"])

ERROS_DEPOSITO: dict[int | str, dict[str, object]] = {
    404: {"model": ErroOut},
    409: {"model": ErroOut},
}


@router.get("")
def listar(auth: AutenticadoDep, db: Db) -> list[CartelaOut]:
    return listar_cartelas(db, auth.usuario.id)


@router.post("", status_code=201, responses={422: {"model": ErroOut}})
def criar(dados: CartelaIn, auth: AutenticadoDep, db: Db, relogio: RelogioDep) -> CartelaOut:
    return criar_cartela(db, auth.usuario.id, dados, relogio.agora_utc())


@router.get("/{cartela_id}", responses={404: {"model": ErroOut}})
def obter(cartela_id: int, auth: AutenticadoDep, db: Db) -> CartelaOut:
    return obter_cartela(db, auth.usuario.id, cartela_id)


@router.post("/{cartela_id}/casas/{casa_id}/deposito", responses=ERROS_DEPOSITO)
def marcar(
    cartela_id: int, casa_id: int, auth: AutenticadoDep, db: Db, relogio: RelogioDep
) -> CartelaOut:
    return depositar(
        db, auth.usuario.id, cartela_id, casa_id, relogio.agora_utc(), relogio.hoje_sp()
    )


@router.delete("/{cartela_id}/casas/{casa_id}/deposito", responses=ERROS_DEPOSITO)
def desmarcar(cartela_id: int, casa_id: int, auth: AutenticadoDep, db: Db) -> CartelaOut:
    return desfazer_deposito(db, auth.usuario.id, cartela_id, casa_id)
