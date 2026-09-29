from fastapi import APIRouter

from app.api.deps import AutenticadoDep, Db, RelogioDep
from app.schemas.divida import DividaIn, DividaOut
from app.schemas.erro import ErroOut
from app.services.divida import criar_divida, listar_dividas, obter_divida

router = APIRouter(prefix="/api/v1/dividas", tags=["dividas"])


@router.get("")
def listar(auth: AutenticadoDep, db: Db) -> list[DividaOut]:
    return listar_dividas(db, auth.usuario.id)


@router.post(
    "",
    status_code=201,
    responses={404: {"model": ErroOut}, 409: {"model": ErroOut}, 422: {"model": ErroOut}},
)
def criar(dados: DividaIn, auth: AutenticadoDep, db: Db, relogio: RelogioDep) -> DividaOut:
    return criar_divida(db, auth.usuario.id, dados, relogio.agora_utc())


@router.get("/{divida_id}", responses={404: {"model": ErroOut}})
def obter(divida_id: int, auth: AutenticadoDep, db: Db) -> DividaOut:
    return obter_divida(db, auth.usuario.id, divida_id)
