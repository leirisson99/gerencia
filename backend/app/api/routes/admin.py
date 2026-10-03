from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import AdministradorDep, Db, RelogioDep, SettingsDep
from app.schemas.admin import (
    DetalheContaOut,
    PaginaEventosOut,
    ResumoAdminOut,
    SenhaTemporariaOut,
    SituacaoConta,
    UsuarioAdminOut,
)
from app.schemas.erro import ErroOut
from app.services.admin import (
    definir_ativo,
    listar_eventos,
    listar_usuarios,
    obter_detalhe,
    obter_resumo,
    resetar_senha,
)

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

ACESSO: dict[int | str, dict[str, object]] = {401: {"model": ErroOut}, 403: {"model": ErroOut}}
ALVO: dict[int | str, dict[str, object]] = {**ACESSO, 404: {"model": ErroOut}}


@router.get("/resumo", responses=ACESSO)
def resumo(admin: AdministradorDep, db: Db, relogio: RelogioDep) -> ResumoAdminOut:
    return obter_resumo(db, relogio.agora_utc())


@router.get("/usuarios", responses=ACESSO)
def usuarios(
    admin: AdministradorDep,
    db: Db,
    busca: str | None = None,
    situacao: SituacaoConta | None = None,
) -> list[UsuarioAdminOut]:
    return [UsuarioAdminOut.model_validate(u) for u in listar_usuarios(db, busca, situacao)]


@router.get("/usuarios/{usuario_id}", responses=ALVO)
def detalhe(
    usuario_id: int, admin: AdministradorDep, db: Db, relogio: RelogioDep, settings: SettingsDep
) -> DetalheContaOut:
    return obter_detalhe(
        db, admin, usuario_id, relogio.agora_utc(), settings.sessao_dias_inatividade
    )


@router.get("/usuarios/{usuario_id}/eventos", responses=ALVO)
def eventos(
    usuario_id: int,
    admin: AdministradorDep,
    db: Db,
    relogio: RelogioDep,
    antes: Annotated[int | None, Query(gt=0)] = None,
) -> PaginaEventosOut:
    return listar_eventos(db, admin, usuario_id, antes, relogio.agora_utc())


@router.post("/usuarios/{usuario_id}/reset-senha", responses=ALVO)
def reset_senha(
    usuario_id: int, admin: AdministradorDep, db: Db, relogio: RelogioDep
) -> SenhaTemporariaOut:
    senha = resetar_senha(db, admin, usuario_id, relogio.agora_utc())
    return SenhaTemporariaOut(senha_temporaria=senha)


@router.post("/usuarios/{usuario_id}/desativar", responses=ALVO)
def desativar(
    usuario_id: int, admin: AdministradorDep, db: Db, relogio: RelogioDep
) -> UsuarioAdminOut:
    usuario = definir_ativo(db, admin, usuario_id, False, relogio.agora_utc())
    return UsuarioAdminOut.model_validate(usuario)


@router.post("/usuarios/{usuario_id}/reativar", responses=ALVO)
def reativar(
    usuario_id: int, admin: AdministradorDep, db: Db, relogio: RelogioDep
) -> UsuarioAdminOut:
    usuario = definir_ativo(db, admin, usuario_id, True, relogio.agora_utc())
    return UsuarioAdminOut.model_validate(usuario)
