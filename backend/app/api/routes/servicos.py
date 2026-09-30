from fastapi import APIRouter

from app.api.deps import ComServicosDep, Db, RelogioDep
from app.domain.servico import SituacaoServico
from app.schemas.erro import ErroOut
from app.schemas.servico import RecebimentoIn, ServicoIn, ServicoOut, ServicoPatch
from app.services.servico import (
    criar_servico,
    desfazer_recebimento,
    editar_servico,
    excluir_servico,
    listar_servicos,
    obter_servico,
    receber_servico,
)

router = APIRouter(prefix="/api/v1/servicos", tags=["servicos"])

ERROS: dict[int | str, dict[str, object]] = {
    403: {"model": ErroOut},
    404: {"model": ErroOut},
    409: {"model": ErroOut},
    422: {"model": ErroOut},
}


@router.get("", responses={403: {"model": ErroOut}})
def listar(
    auth: ComServicosDep, db: Db, relogio: RelogioDep, situacao: SituacaoServico | None = None
) -> list[ServicoOut]:
    return listar_servicos(db, auth.usuario.id, relogio.hoje_sp(), situacao)


@router.post("", status_code=201, responses=ERROS)
def criar(dados: ServicoIn, auth: ComServicosDep, db: Db, relogio: RelogioDep) -> ServicoOut:
    return criar_servico(db, auth.usuario.id, dados, relogio.agora_utc(), relogio.hoje_sp())


@router.get("/{servico_id}", responses=ERROS)
def obter(servico_id: int, auth: ComServicosDep, db: Db, relogio: RelogioDep) -> ServicoOut:
    return obter_servico(db, auth.usuario.id, servico_id, relogio.hoje_sp())


@router.patch("/{servico_id}", responses=ERROS)
def editar(
    servico_id: int, dados: ServicoPatch, auth: ComServicosDep, db: Db, relogio: RelogioDep
) -> ServicoOut:
    return editar_servico(
        db, auth.usuario.id, servico_id, dados, relogio.agora_utc(), relogio.hoje_sp()
    )


@router.delete("/{servico_id}", status_code=204, responses=ERROS)
def excluir(servico_id: int, auth: ComServicosDep, db: Db) -> None:
    excluir_servico(db, auth.usuario.id, servico_id)


@router.post("/{servico_id}/recebimento", responses=ERROS)
def receber(
    servico_id: int, dados: RecebimentoIn, auth: ComServicosDep, db: Db, relogio: RelogioDep
) -> ServicoOut:
    return receber_servico(
        db, auth.usuario.id, servico_id, dados, relogio.agora_utc(), relogio.hoje_sp()
    )


@router.delete("/{servico_id}/recebimento", responses=ERROS)
def desfazer(servico_id: int, auth: ComServicosDep, db: Db, relogio: RelogioDep) -> ServicoOut:
    return desfazer_recebimento(
        db, auth.usuario.id, servico_id, relogio.agora_utc(), relogio.hoje_sp()
    )
