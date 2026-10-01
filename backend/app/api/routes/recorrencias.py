from fastapi import APIRouter

from app.api.deps import AutenticadoDep, Db, RelogioDep
from app.schemas.erro import ErroOut
from app.schemas.recorrencia import RecorrenciaIn, RecorrenciaOut, RecorrenciaPatch
from app.services.recorrencia import criar_recorrencia, editar_recorrencia, listar_recorrencias

router = APIRouter(prefix="/api/v1/recorrencias", tags=["recorrencias"])

ERROS_ESCRITA: dict[int | str, dict[str, object]] = {
    404: {"model": ErroOut},
    422: {"model": ErroOut},
}


@router.get("")
def listar(auth: AutenticadoDep, db: Db) -> list[RecorrenciaOut]:
    return [RecorrenciaOut.model_validate(r) for r in listar_recorrencias(db, auth.usuario.id)]


@router.post("", status_code=201, responses=ERROS_ESCRITA)
def criar(
    dados: RecorrenciaIn, auth: AutenticadoDep, db: Db, relogio: RelogioDep
) -> RecorrenciaOut:
    recorrencia = criar_recorrencia(
        db, auth.usuario.id, dados, relogio.agora_utc(), relogio.hoje_sp()
    )
    return RecorrenciaOut.model_validate(recorrencia)


@router.patch("/{recorrencia_id}", responses=ERROS_ESCRITA)
def editar(
    recorrencia_id: int, dados: RecorrenciaPatch, auth: AutenticadoDep, db: Db
) -> RecorrenciaOut:
    recorrencia = editar_recorrencia(db, auth.usuario.id, recorrencia_id, dados)
    return RecorrenciaOut.model_validate(recorrencia)
