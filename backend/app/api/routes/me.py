from fastapi import APIRouter

from app.api.deps import AutenticadoDep, AutenticadoPermitindoTrocaDep, Db, RelogioDep
from app.schemas.erro import ErroOut
from app.schemas.usuario import PerfilIn, TrocaSenhaIn, UsuarioOut
from app.services.auth import trocar_senha
from app.services.perfil import atualizar_perfil

router = APIRouter(prefix="/api/v1", tags=["me"])


@router.get("/me", responses={401: {"model": ErroOut}, 403: {"model": ErroOut}})
def obter_me(auth: AutenticadoDep) -> UsuarioOut:
    return UsuarioOut.model_validate(auth.usuario)


@router.patch(
    "/me",
    responses={
        401: {"model": ErroOut},
        403: {"model": ErroOut},
        409: {"model": ErroOut},  # troca de tipo de renda que deixaria lançamentos fora de ciclo
        422: {"model": ErroOut},
    },
)
def editar_me(dados: PerfilIn, auth: AutenticadoDep, db: Db, relogio: RelogioDep) -> UsuarioOut:
    usuario = atualizar_perfil(db, auth.usuario, dados, relogio.agora_utc(), relogio.hoje_sp())
    return UsuarioOut.model_validate(usuario)


@router.put(
    "/me/senha",
    status_code=204,
    responses={400: {"model": ErroOut}, 401: {"model": ErroOut}, 422: {"model": ErroOut}},
)
def alterar_senha(
    dados: TrocaSenhaIn,
    auth: AutenticadoPermitindoTrocaDep,
    db: Db,
    relogio: RelogioDep,
) -> None:
    trocar_senha(
        db, auth.usuario, auth.sessao, dados.senha_atual, dados.nova_senha, relogio.agora_utc()
    )
