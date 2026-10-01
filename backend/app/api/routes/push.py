from fastapi import APIRouter

from app.api.deps import AutenticadoDep, Db, SettingsDep
from app.schemas.erro import ErroOut
from app.schemas.push import ChavePushOut, InscricaoIn, InscricaoRemoverIn
from app.services.push import chave_publica, inscrever, remover_inscricao

router = APIRouter(prefix="/api/v1/push", tags=["push"])


@router.get("/chave", responses={401: {"model": ErroOut}, 503: {"model": ErroOut}})
def obter_chave(_: AutenticadoDep, settings: SettingsDep) -> ChavePushOut:
    return ChavePushOut(chave_publica=chave_publica(settings))


@router.put(
    "/inscricao",
    status_code=204,
    responses={401: {"model": ErroOut}, 422: {"model": ErroOut}, 503: {"model": ErroOut}},
)
def ativar(dados: InscricaoIn, auth: AutenticadoDep, db: Db, settings: SettingsDep) -> None:
    """Ativa as notificações neste aparelho; chamar de novo só atualiza as chaves."""
    inscrever(db, auth.usuario.id, dados, settings)


@router.delete(
    "/inscricao", status_code=204, responses={401: {"model": ErroOut}, 404: {"model": ErroOut}}
)
def desativar(dados: InscricaoRemoverIn, auth: AutenticadoDep, db: Db) -> None:
    remover_inscricao(db, auth.usuario.id, dados.endpoint)
