from fastapi import APIRouter

from app.api.deps import AutenticadoDep, Db, RelogioDep
from app.schemas.erro import ErroOut
from app.schemas.importacao import BancoOut, ImportacaoIn, ImportacaoOut, PreviaIn, PreviaOut
from app.services.importacao import confirmar, listar_bancos, previa

router = APIRouter(prefix="/api/v1/importacoes", tags=["importacoes"])

ERROS_LEITURA: dict[int | str, dict[str, object]] = {
    413: {"model": ErroOut},
    422: {"model": ErroOut},
}
ERROS_ESCRITA: dict[int | str, dict[str, object]] = {
    404: {"model": ErroOut},
    409: {"model": ErroOut},
    422: {"model": ErroOut},
}


@router.get("/bancos", responses={401: {"model": ErroOut}, 403: {"model": ErroOut}})
def bancos(auth: AutenticadoDep) -> list[BancoOut]:
    return listar_bancos()


@router.post("/previa", responses=ERROS_LEITURA)
def criar_previa(dados: PreviaIn, auth: AutenticadoDep, db: Db) -> PreviaOut:
    """Lê o extrato e classifica as linhas. Nada é gravado."""
    return previa(db, auth.usuario.id, dados)


@router.post("", status_code=201, responses=ERROS_ESCRITA)
def importar(
    dados: ImportacaoIn, auth: AutenticadoDep, db: Db, relogio: RelogioDep
) -> ImportacaoOut:
    """Grava as linhas confirmadas, todas ou nenhuma."""
    return confirmar(db, auth.usuario.id, dados, relogio.agora_utc(), relogio.hoje_sp())
