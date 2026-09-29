from datetime import date

from fastapi import APIRouter

from app.api.deps import AutenticadoDep, Db
from app.schemas.ciclo import CicloOut, SugestaoSalarioOut
from app.schemas.erro import ErroOut
from app.schemas.lancamento import LancamentoOut
from app.schemas.resumo import ResumoCicloOut
from app.services.ciclo import (
    lancamentos_do_ciclo,
    obter_ciclo_atual,
    obter_ciclo_da_data,
    sugestao_salario,
)
from app.services.resumo import resumo_do_ciclo

router = APIRouter(prefix="/api/v1", tags=["ciclos"])

SEM_CICLO: dict[int | str, dict[str, object]] = {404: {"model": ErroOut}}


# Declarada antes de /ciclos/{data} para "atual" não ser lido como data.
@router.get("/ciclos/atual", responses=SEM_CICLO)
def atual(auth: AutenticadoDep, db: Db) -> CicloOut:
    return CicloOut.model_validate(obter_ciclo_atual(db, auth.usuario.id))


@router.get("/ciclos/{data}", responses=SEM_CICLO)
def da_data(data: date, auth: AutenticadoDep, db: Db) -> CicloOut:
    return CicloOut.model_validate(obter_ciclo_da_data(db, auth.usuario.id, data))


@router.get("/ciclos/{data}/lancamentos", responses=SEM_CICLO)
def lancamentos(data: date, auth: AutenticadoDep, db: Db) -> list[LancamentoOut]:
    return [
        LancamentoOut.model_validate(lanc)
        for lanc in lancamentos_do_ciclo(db, auth.usuario.id, data)
    ]


@router.get("/ciclos/{data}/resumo", responses=SEM_CICLO)
def resumo(data: date, auth: AutenticadoDep, db: Db) -> ResumoCicloOut:
    return resumo_do_ciclo(db, auth.usuario.id, data)


@router.get("/salarios/sugestao")
def sugestao(auth: AutenticadoDep, db: Db) -> SugestaoSalarioOut:
    return SugestaoSalarioOut(valor=sugestao_salario(db, auth.usuario.id))
