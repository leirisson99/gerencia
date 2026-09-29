from fastapi import APIRouter

from app.api.deps import AdministradorDep, Db, RelogioDep
from app.schemas.admin import SenhaTemporariaOut, UsuarioAdminOut
from app.schemas.erro import ErroOut
from app.services.admin import listar_usuarios, resetar_senha

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

ACESSO: dict[int | str, dict[str, object]] = {401: {"model": ErroOut}, 403: {"model": ErroOut}}


@router.get("/usuarios", responses=ACESSO)
def usuarios(admin: AdministradorDep, db: Db, busca: str | None = None) -> list[UsuarioAdminOut]:
    return [UsuarioAdminOut.model_validate(u) for u in listar_usuarios(db, busca)]


@router.post("/usuarios/{usuario_id}/reset-senha", responses={**ACESSO, 404: {"model": ErroOut}})
def reset_senha(
    usuario_id: int, admin: AdministradorDep, db: Db, relogio: RelogioDep
) -> SenhaTemporariaOut:
    senha = resetar_senha(db, admin, usuario_id, relogio.agora_utc())
    return SenhaTemporariaOut(senha_temporaria=senha)
