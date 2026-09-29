from dataclasses import dataclass
from typing import Annotated

from fastapi import Cookie, Depends, Response
from sqlalchemy.orm import Session

from app.api.cookies import definir_cookie_sessao
from app.config import Settings, get_settings
from app.db import get_db
from app.erros import ErroApi
from app.models import Sessao, Usuario
from app.relogio import Relogio, get_relogio
from app.services.sessao import resolver_sessao

Db = Annotated[Session, Depends(get_db)]
RelogioDep = Annotated[Relogio, Depends(get_relogio)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


@dataclass(frozen=True)
class Autenticado:
    usuario: Usuario
    sessao: Sessao


def autenticacao_permitindo_troca(
    response: Response,
    db: Db,
    relogio: RelogioDep,
    settings: SettingsDep,
    sessao: Annotated[str | None, Cookie()] = None,
) -> Autenticado:
    """Exige sessão válida, mesmo com troca de senha pendente."""
    if not sessao:
        raise ErroApi(401, "nao_autenticado", "Entre para continuar.")
    registro = resolver_sessao(db, sessao, relogio.agora_utc(), settings.sessao_dias_inatividade)
    if registro is None:
        raise ErroApi(401, "nao_autenticado", "Entre para continuar.")
    # Renova o cookie a cada uso: a expiração conta a partir do último uso.
    definir_cookie_sessao(response, sessao, settings)
    return Autenticado(usuario=registro.usuario, sessao=registro)


def autenticacao(
    auth: Annotated[Autenticado, Depends(autenticacao_permitindo_troca)],
) -> Autenticado:
    """Exige sessão válida e nenhuma troca de senha pendente."""
    if auth.usuario.troca_senha_obrigatoria:
        raise ErroApi(403, "troca_senha_obrigatoria", "Troque sua senha para continuar.")
    return auth


AutenticadoDep = Annotated[Autenticado, Depends(autenticacao)]
AutenticadoPermitindoTrocaDep = Annotated[Autenticado, Depends(autenticacao_permitindo_troca)]
