from fastapi import APIRouter

from app.api.deps import AutenticadoDep, Db
from app.schemas.categoria import CategoriaIn, CategoriaOut, CategoriaPatch
from app.schemas.erro import ErroOut
from app.services.categoria import criar_categoria, editar_categoria, listar_categorias

router = APIRouter(prefix="/api/v1/categorias", tags=["categorias"])

ERROS_ESCRITA: dict[int | str, dict[str, object]] = {
    404: {"model": ErroOut},
    409: {"model": ErroOut},
    422: {"model": ErroOut},
}


@router.get("", responses={401: {"model": ErroOut}, 403: {"model": ErroOut}})
def listar(auth: AutenticadoDep, db: Db, incluir_inativas: bool = False) -> list[CategoriaOut]:
    categorias = listar_categorias(db, auth.usuario.id, incluir_inativas)
    return [CategoriaOut.model_validate(c) for c in categorias]


@router.post("", status_code=201, responses=ERROS_ESCRITA)
def criar(dados: CategoriaIn, auth: AutenticadoDep, db: Db) -> CategoriaOut:
    return CategoriaOut.model_validate(criar_categoria(db, auth.usuario.id, dados))


@router.patch("/{categoria_id}", responses=ERROS_ESCRITA)
def editar(categoria_id: int, dados: CategoriaPatch, auth: AutenticadoDep, db: Db) -> CategoriaOut:
    return CategoriaOut.model_validate(editar_categoria(db, auth.usuario.id, categoria_id, dados))
