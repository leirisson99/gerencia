from datetime import date, datetime

from sqlalchemy import func, not_, select
from sqlalchemy.orm import Session

from app.domain.ciclo import ProblemaCobertura, ciclo_atual, verificar_cobertura
from app.erros import MENSAGEM_VALIDACAO, ErroApi
from app.models import Categoria, Lancamento
from app.models.lancamento import STATUS_REALIZADO
from app.schemas.lancamento import LancamentoIn, LancamentoPatch
from app.services.categoria import obter_categoria_ativa
from app.services.ciclo import condicao_salario, datas_de_salario, travar_escritas
from app.services.recorrencia import gerar_previstos


def obter_lancamento(db: Session, usuario_id: int, lancamento_id: int) -> Lancamento:
    lancamento = db.scalar(
        select(Lancamento).where(
            Lancamento.id == lancamento_id, Lancamento.usuario_id == usuario_id
        )
    )
    if lancamento is None:
        raise ErroApi(404, "nao_encontrado", "Lançamento não encontrado.")
    return lancamento


def _validar_salario(categoria: Categoria, status: str, data: date, hoje: date) -> None:
    if not categoria.e_salario:
        return
    if status != STATUS_REALIZADO:
        raise ErroApi(
            422, "validacao", MENSAGEM_VALIDACAO, campos={"status": "O salário é sempre realizado."}
        )
    if data > hoje:
        raise ErroApi(
            422,
            "validacao",
            MENSAGEM_VALIDACAO,
            campos={"data": "O salário é lançado quando entra; a data não pode ser futura."},
        )


def _menor_data_dos_outros(db: Session, usuario_id: int, ignorar_id: int | None) -> date | None:
    consulta = (
        select(func.min(Lancamento.data))
        .join(Categoria, Lancamento.categoria_id == Categoria.id)
        .where(Lancamento.usuario_id == usuario_id, not_(condicao_salario()))
    )
    if ignorar_id is not None:
        consulta = consulta.where(Lancamento.id != ignorar_id)
    return db.scalar(consulta)


def _problema_depois_da_mudanca(
    db: Session,
    usuario_id: int,
    ignorar_id: int | None,
    novo: tuple[bool, date] | None,
) -> tuple[ProblemaCobertura, list[date]] | None:
    """Verifica a cobertura no estado resultante: sem `ignorar_id` e com `novo`.

    `novo` é (abre_ciclo, data) do lançamento como ficará, ou None numa exclusão.
    """
    salarios = datas_de_salario(db, usuario_id, ignorar_id)
    menor_outros = _menor_data_dos_outros(db, usuario_id, ignorar_id)
    if novo is not None:
        abre_ciclo, data = novo
        if abre_ciclo:
            salarios.append(data)
        elif menor_outros is None or data < menor_outros:
            menor_outros = data
    problema = verificar_cobertura(salarios, menor_outros)
    return (problema, salarios) if problema else None


def _erro_de_cobertura(problema: ProblemaCobertura, salarios: list[date]) -> ErroApi:
    if problema is ProblemaCobertura.SEM_SALARIO:
        return ErroApi(409, "salario_necessario", "Lance seu salário para abrir o primeiro ciclo.")
    inicio = min(salarios).strftime("%d/%m/%Y")
    return ErroApi(
        409,
        "antes_do_primeiro_ciclo",
        f"A data é anterior ao primeiro ciclo, que começa em {inicio}.",
    )


def _erro_sem_ciclo() -> ErroApi:
    return ErroApi(
        409, "lancamentos_sem_ciclo", "A mudança deixaria lançamentos fora de qualquer ciclo."
    )


def verificar_novos_lancamentos(db: Session, usuario_id: int, menor_data: date) -> None:
    """Recusa lançamentos (que não são salário) a partir de `menor_data` fora de ciclo."""
    resultado = _problema_depois_da_mudanca(db, usuario_id, None, (False, menor_data))
    if resultado:
        raise _erro_de_cobertura(*resultado)


def criar_lancamento(
    db: Session, usuario_id: int, dados: LancamentoIn, agora: datetime, hoje: date
) -> Lancamento:
    travar_escritas(db, usuario_id)
    categoria = obter_categoria_ativa(db, usuario_id, dados.categoria_id)
    _validar_salario(categoria, dados.status, dados.data, hoje)

    abre_ciclo = categoria.e_salario and dados.status == STATUS_REALIZADO
    resultado = _problema_depois_da_mudanca(db, usuario_id, None, (abre_ciclo, dados.data))
    if resultado:
        raise _erro_de_cobertura(*resultado)

    salarios = datas_de_salario(db, usuario_id) if abre_ciclo else []
    # Só um salário posterior a todos os outros abre um ciclo novo (e gera os previstos).
    abre_ciclo_novo = abre_ciclo and (not salarios or dados.data > max(salarios))

    lancamento = Lancamento(
        usuario_id=usuario_id,
        categoria_id=categoria.id,
        data=dados.data,
        valor=dados.valor,
        tipo=categoria.tipo,
        descricao=dados.descricao,
        status=dados.status,
        criado_em=agora,
        atualizado_em=agora,
    )
    db.add(lancamento)
    if abre_ciclo_novo:
        ciclo = ciclo_atual([*salarios, dados.data])
        assert ciclo is not None
        gerar_previstos(db, usuario_id, ciclo, agora)
    db.commit()
    return lancamento


def editar_lancamento(
    db: Session,
    usuario_id: int,
    lancamento_id: int,
    dados: LancamentoPatch,
    agora: datetime,
    hoje: date,
) -> Lancamento:
    travar_escritas(db, usuario_id)
    lancamento = obter_lancamento(db, usuario_id, lancamento_id)
    enviados = dados.model_fields_set
    if not enviados:
        return lancamento
    muda_categoria = (
        dados.categoria_id is not None and dados.categoria_id != lancamento.categoria_id
    )
    if lancamento.divida_id is not None and muda_categoria:
        raise ErroApi(
            422,
            "validacao",
            MENSAGEM_VALIDACAO,
            campos={"categoria_id": "A parcela fica na categoria da dívida."},
        )

    categoria = (
        obter_categoria_ativa(db, usuario_id, dados.categoria_id)
        if "categoria_id" in enviados and dados.categoria_id is not None
        else lancamento.categoria
    )
    data = dados.data if dados.data is not None else lancamento.data
    status = dados.status if dados.status is not None else lancamento.status
    _validar_salario(categoria, status, data, hoje)

    era_salario = lancamento.abre_ciclo
    sera_salario = categoria.e_salario and status == STATUS_REALIZADO
    resultado = _problema_depois_da_mudanca(db, usuario_id, lancamento.id, (sera_salario, data))
    if resultado:
        if era_salario or sera_salario:
            raise _erro_sem_ciclo()
        raise _erro_de_cobertura(*resultado)

    lancamento.categoria = categoria
    lancamento.tipo = categoria.tipo
    lancamento.data = data
    lancamento.status = status
    if dados.valor is not None:
        lancamento.valor = dados.valor
    if "descricao" in enviados:
        lancamento.descricao = dados.descricao
    lancamento.atualizado_em = agora
    db.commit()
    return lancamento


def excluir_lancamento(db: Session, usuario_id: int, lancamento_id: int) -> None:
    travar_escritas(db, usuario_id)
    lancamento = obter_lancamento(db, usuario_id, lancamento_id)
    if lancamento.divida_id is not None:
        raise ErroApi(409, "parcela_de_divida", "Parcelas de dívida não podem ser excluídas.")
    if _problema_depois_da_mudanca(db, usuario_id, lancamento.id, None):
        raise _erro_sem_ciclo()
    db.delete(lancamento)
    db.commit()
