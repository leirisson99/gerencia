from fastapi import APIRouter

from app.api.deps import AutenticadoDep, Db, RelogioDep
from app.schemas.erro import ErroOut
from app.schemas.lembrete import LembreteLivreIn, LembreteLivreOut, LembreteLivrePatch, LembretesOut
from app.services.lembrete import (
    criar_livre,
    editar_livre,
    excluir_livre,
    listar_lembretes,
    listar_livres,
)

router = APIRouter(prefix="/api/v1/lembretes", tags=["lembretes"])

ERROS: dict[int | str, dict[str, object]] = {
    401: {"model": ErroOut},
    404: {"model": ErroOut},
    422: {"model": ErroOut},
}


@router.get("", responses={401: {"model": ErroOut}})
def listar(auth: AutenticadoDep, db: Db, relogio: RelogioDep) -> LembretesOut:
    """Contas a pagar, valores a receber e lembretes livres atrasados e até hoje + 3 dias."""
    return listar_lembretes(db, auth.usuario.id, relogio.hoje_sp())


@router.get("/livres", responses={401: {"model": ErroOut}})
def listar_todos_livres(auth: AutenticadoDep, db: Db) -> list[LembreteLivreOut]:
    """Todos os lembretes livres, inclusive concluídos e futuros, por data."""
    return [LembreteLivreOut.model_validate(livre) for livre in listar_livres(db, auth.usuario.id)]


@router.post("/livres", status_code=201, responses=ERROS)
def criar(
    dados: LembreteLivreIn, auth: AutenticadoDep, db: Db, relogio: RelogioDep
) -> LembreteLivreOut:
    return LembreteLivreOut.model_validate(
        criar_livre(db, auth.usuario.id, dados, relogio.agora_utc())
    )


@router.patch("/livres/{lembrete_id}", responses=ERROS)
def editar(
    lembrete_id: int,
    dados: LembreteLivrePatch,
    auth: AutenticadoDep,
    db: Db,
    relogio: RelogioDep,
) -> LembreteLivreOut:
    return LembreteLivreOut.model_validate(
        editar_livre(db, auth.usuario.id, lembrete_id, dados, relogio.agora_utc())
    )


@router.delete("/livres/{lembrete_id}", status_code=204, responses=ERROS)
def excluir(lembrete_id: int, auth: AutenticadoDep, db: Db) -> None:
    excluir_livre(db, auth.usuario.id, lembrete_id)
