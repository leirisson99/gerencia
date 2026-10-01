from datetime import date, datetime

from sqlalchemy import exists, or_, select
from sqlalchemy.orm import Session

from app.domain.categoria import NOME_SALARIO
from app.domain.ciclo import ProblemaTroca, verificar_troca_tipo_renda
from app.erros import ErroApi
from app.models import Categoria, Lancamento, Servico, Usuario
from app.models.lancamento import STATUS_PREVISTO
from app.schemas.usuario import PerfilIn
from app.services.auth import checar_data_nascimento
from app.services.ciclo import datas_de_salario, travar_escritas
from app.services.lancamento import menor_data_dos_outros


def _tem_salario_irregular(db: Session, usuario_id: int, hoje: date) -> bool:
    """ "Salário" previsto ou com data futura: aceito para o prestador, não para o CLT."""
    return (
        db.scalar(
            select(
                exists().where(
                    Lancamento.usuario_id == usuario_id,
                    Lancamento.categoria_id == Categoria.id,
                    Categoria.sistema,
                    Categoria.nome == NOME_SALARIO,
                    or_(Lancamento.status == STATUS_PREVISTO, Lancamento.data > hoje),
                )
            )
        )
        or False
    )


def _tem_servico_pendente(db: Session, usuario_id: int) -> bool:
    return (
        db.scalar(
            select(
                exists().where(
                    Servico.usuario_id == usuario_id,
                    Servico.lancamento_id == Lancamento.id,
                    Lancamento.status == STATUS_PREVISTO,
                )
            )
        )
        or False
    )


def _checar_troca_tipo_renda(db: Session, usuario: Usuario, novo: str, hoje: date) -> None:
    atual = travar_escritas(db, usuario.id)
    problema = verificar_troca_tipo_renda(
        atual,
        novo,
        datas_de_salario(db, usuario.id),
        menor_data_dos_outros(db, usuario.id, None),
        _tem_salario_irregular(db, usuario.id, hoje),
        servicos_pendentes=_tem_servico_pendente(db, usuario.id),
    )
    if problema is ProblemaTroca.SERVICOS_PENDENTES:
        raise ErroApi(
            409,
            "servicos_pendentes",
            "Há serviços a receber. Receba ou exclua esses serviços antes de trocar.",
        )
    if problema is ProblemaTroca.SALARIO_INVALIDO:
        raise ErroApi(
            409,
            "salario_invalido",
            "Como CLT, o salário é sempre realizado e não tem data futura. "
            "Ajuste os lançamentos em Salário antes de trocar.",
        )
    if problema is ProblemaTroca.LANCAMENTOS_SEM_CICLO:
        raise ErroApi(
            409,
            "lancamentos_sem_ciclo",
            "Lance o salário antes: há lançamentos fora de um ciclo de salário.",
        )


def atualizar_perfil(
    db: Session, usuario: Usuario, dados: PerfilIn, agora: datetime, hoje: date
) -> Usuario:
    enviados = dados.model_fields_set
    if not enviados:
        return usuario
    if "data_nascimento" in enviados:
        checar_data_nascimento(dados.data_nascimento, hoje)
    if "tipo_renda" in enviados and dados.tipo_renda != usuario.tipo_renda:
        assert dados.tipo_renda is not None, "null é recusado no schema"
        _checar_troca_tipo_renda(db, usuario, dados.tipo_renda, hoje)
    for campo in enviados:
        setattr(usuario, campo, getattr(dados, campo))
    usuario.atualizado_em = agora
    db.commit()
    return usuario
