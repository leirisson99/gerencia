from fastapi import APIRouter, Response

from app.api.cookies import apagar_cookie_sessao, definir_cookie_sessao
from app.api.deps import AutenticadoPermitindoTrocaDep, Db, RelogioDep, SettingsDep
from app.schemas.erro import ErroOut
from app.schemas.usuario import CadastroIn, LoginIn, UsuarioOut
from app.services.auth import cadastrar, entrar, sair

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post(
    "/cadastro",
    status_code=201,
    responses={409: {"model": ErroOut}, 422: {"model": ErroOut}},
)
def cadastro(
    dados: CadastroIn,
    response: Response,
    db: Db,
    relogio: RelogioDep,
    settings: SettingsDep,
) -> UsuarioOut:
    usuario, token = cadastrar(db, dados, relogio.agora_utc(), relogio.hoje_sp())
    definir_cookie_sessao(response, token, settings)
    return UsuarioOut.model_validate(usuario)


@router.post(
    "/login",
    responses={401: {"model": ErroOut}, 422: {"model": ErroOut}, 429: {"model": ErroOut}},
)
def login(
    dados: LoginIn,
    response: Response,
    db: Db,
    relogio: RelogioDep,
    settings: SettingsDep,
) -> UsuarioOut:
    usuario, token = entrar(db, dados.email, dados.senha, relogio.agora_utc())
    definir_cookie_sessao(response, token, settings)
    return UsuarioOut.model_validate(usuario)


@router.post("/logout", status_code=204, responses={401: {"model": ErroOut}})
def logout(
    auth: AutenticadoPermitindoTrocaDep,
    response: Response,
    db: Db,
    settings: SettingsDep,
) -> None:
    sair(db, auth.sessao)
    # Descarta a renovação feita pela autenticação; só o cookie apagado deve sair.
    del response.headers["set-cookie"]
    apagar_cookie_sessao(response, settings)
