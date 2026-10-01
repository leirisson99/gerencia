from fastapi import APIRouter

from app.api.deps import AutenticadoDep, Db, RelogioDep
from app.schemas.erro import ErroOut
from app.schemas.lembrete import LembretesOut
from app.services.lembrete import listar_lembretes

router = APIRouter(prefix="/api/v1/lembretes", tags=["lembretes"])


@router.get("", responses={401: {"model": ErroOut}})
def listar(auth: AutenticadoDep, db: Db, relogio: RelogioDep) -> LembretesOut:
    """Contas a pagar e valores a receber atrasados e até hoje + 3 dias."""
    return listar_lembretes(db, auth.usuario.id, relogio.hoje_sp())
