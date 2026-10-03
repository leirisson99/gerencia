from datetime import date, datetime

from sqlalchemy import exists, or_, select
from sqlalchemy.orm import Session

from app.domain.categoria import NOME_SALARIO
from app.domain.ciclo import ProblemaTroca, verificar_troca_tipo_renda
from app.domain.usuario import CARTEIRA_PADRAO, verificar_pj
from app.erros import ErroApi
from app.models import Categoria, Lancamento, Recorrencia, Retirada, Servico, Usuario
from app.models.lancamento import STATUS_PREVISTO
from app.schemas.usuario import PerfilIn
from app.services.auth import checar_conta_editavel, checar_data_nascimento
from app.services.categoria import garantir_categorias_pj
from app.services.ciclo import datas_de_salario, travar_escritas
from app.services.evento_uso import registrar
from app.services.lancamento import menor_data_dos_outros


def _tem_salario_irregular(db: Session, usuario_id: int, hoje: date) -> bool:
    """ "Salário" previsto ou com data futura: aceito para o prestador, não para o CLT."""
    return (
        db.scalar(
            select(
                exists().where(
                    Lancamento.usuario_id == usuario_id,
                    Lancamento.carteira == CARTEIRA_PADRAO,
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


def _tem_dados_pj(db: Session, usuario_id: int) -> bool:
    """Lançamento, recorrência ou retirada na PJ: impedem desligar a carteira."""
    return bool(
        db.scalar(
            select(
                exists().where(Lancamento.usuario_id == usuario_id, Lancamento.carteira == "pj")
                | exists().where(Recorrencia.usuario_id == usuario_id, Recorrencia.carteira == "pj")
                | exists().where(Retirada.usuario_id == usuario_id)
            )
        )
    )


def _decidir_pj(db: Session, usuario: Usuario, dados: PerfilIn) -> bool:
    """Novo valor de `tem_pj`. Trocar para `clt` desliga a PJ junto, se ela estiver vazia."""
    enviados = dados.model_fields_set
    tipo_novo = dados.tipo_renda if "tipo_renda" in enviados else usuario.tipo_renda
    assert tipo_novo is not None, "null é recusado no schema"
    if "tem_pj" in enviados:
        assert dados.tem_pj is not None, "null é recusado no schema"
        tem_pj_novo = dados.tem_pj
    else:
        tem_pj_novo = usuario.tem_pj and tipo_novo != "clt"
    if tem_pj_novo == usuario.tem_pj and not (tem_pj_novo and tipo_novo == "clt"):
        return tem_pj_novo
    travar_escritas(db, usuario.id)
    problema = verificar_pj(tem_pj_novo, tipo_novo, _tem_dados_pj(db, usuario.id))
    if problema == "tipo_sem_pj":
        raise ErroApi(
            409,
            "tipo_sem_pj",
            "A carteira PJ é para quem presta serviço: mude o tipo de renda para CLT e "
            "prestador de serviço.",
        )
    if problema == "pj_com_dados":
        raise ErroApi(
            409,
            "pj_com_dados",
            "Há lançamentos, recorrências ou retiradas na PJ. Remova-os antes de desligar a PJ.",
        )
    if tem_pj_novo and not usuario.tem_pj:
        garantir_categorias_pj(db, usuario.id)
    return tem_pj_novo


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
    checar_conta_editavel(usuario)
    enviados = dados.model_fields_set
    if not enviados:
        return usuario
    if "data_nascimento" in enviados:
        checar_data_nascimento(dados.data_nascimento, hoje)
    if "tipo_renda" in enviados and dados.tipo_renda != usuario.tipo_renda:
        assert dados.tipo_renda is not None, "null é recusado no schema"
        _checar_troca_tipo_renda(db, usuario, dados.tipo_renda, hoje)
    tem_pj = _decidir_pj(db, usuario, dados)
    for campo in enviados:
        setattr(usuario, campo, getattr(dados, campo))
    usuario.tem_pj = tem_pj
    usuario.atualizado_em = agora
    registrar(db, usuario.id, "perfil_atualizado")
    db.commit()
    return usuario
