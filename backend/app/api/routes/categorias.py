from fastapi import APIRouter

from app.api.deps import AutenticadoDep, Db
from app.schemas.categoria import CategoriaOut
from app.schemas.erro import ErroOut
from app.services.categoria import listar_categorias

router = APIRouter(prefix="/api/v1", tags=["categorias"])


@router.get("/categorias", responses={401: {"model": ErroOut}, 403: {"model": ErroOut}})
def listar(auth: AutenticadoDep, db: Db) -> list[CategoriaOut]:
    categorias = listar_categorias(db, auth.usuario.id)
    return [CategoriaOut.model_validate(c) for c in categorias]
