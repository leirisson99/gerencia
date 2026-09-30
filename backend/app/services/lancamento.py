from datetime import date, datetime

from sqlalchemy import exists, func, not_, select
from sqlalchemy.orm import Session

from app.domain.ciclo import ProblemaCobertura, ciclo_atual, ciclo_mensal, verificar_cobertura
from app.domain.usuario import ciclo_pelo_mes, tem_servicos
from app.erros import MENSAGEM_VALIDACAO, ErroApi
from app.models import Casa, Categoria, Lancamento
from app.models.lancamento import STATUS_REALIZADO
from app.schemas.lancamento import AvisoLimiteOut, LancamentoIn, LancamentoPatch
from app.services.categoria import obter_categoria_ativa
from app.services.ciclo import (
    condicao_salario,
    datas_de_salario,
    tipo_renda_do_usuario,
    travar_escritas,
)
from app.services.limite import avaliar_aviso, usado_no_ciclo
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


def menor_data_dos_outros(db: Session, usuario_id: int, ignorar_id: int | None) -> date | None:
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

    `novo` é (abre_ciclo, data) do lançamento como ficará, ou None numa exclusão. No ciclo pelo
    mês (prestador), todo lançamento cai num ciclo.
    """
    if ciclo_pelo_mes(tipo_renda_do_usuario(db, usuario_id)):
        return None
    salarios = datas_de_salario(db, usuario_id, ignorar_id)
    menor_outros = menor_data_dos_outros(db, usuario_id, ignorar_id)
    if novo is not None:
        abre_ciclo, data = novo
        if abre_ciclo:
            salarios.append(data)
        elif menor_outros is None or data < menor_outros:
            menor_outros = data
    problema = verificar_cobertura(salarios, menor_outros)
    return (problema, salarios) if problema else None


def erro_de_cobertura(problema: ProblemaCobertura, salarios: list[date]) -> ErroApi:
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


def _e_deposito_de_cartela(db: Session, lancamento_id: int) -> bool:
    return db.scalar(select(exists().where(Casa.lancamento_id == lancamento_id))) or False


def _e_de_servico(lancamento: Lancamento, tipo_renda: str) -> bool:
    """Entrada de serviço a receber: o serviço a controla, enquanto o dono tiver serviços."""
    return lancamento.servico_id is not None and tem_servicos(tipo_renda)


def verificar_novos_lancamentos(db: Session, usuario_id: int, menor_data: date) -> None:
    """Recusa lançamentos (que não são salário) a partir de `menor_data` fora de ciclo."""
    resultado = _problema_depois_da_mudanca(db, usuario_id, None, (False, menor_data))
    if resultado:
        raise erro_de_cobertura(*resultado)


def criar_lancamento(
    db: Session, usuario_id: int, dados: LancamentoIn, agora: datetime, hoje: date
) -> tuple[Lancamento, AvisoLimiteOut | None]:
    """Cria o lançamento; devolve também o aviso se a categoria piorar de situação no ciclo."""
    pelo_mes = ciclo_pelo_mes(travar_escritas(db, usuario_id))
    categoria = obter_categoria_ativa(db, usuario_id, dados.categoria_id)
    if not pelo_mes:
        _validar_salario(categoria, dados.status, dados.data, hoje)

    # Para o prestador, "Salário" é uma entrada comum.
    abre_ciclo = not pelo_mes and categoria.e_salario and dados.status == STATUS_REALIZADO
    resultado = _problema_depois_da_mudanca(db, usuario_id, None, (abre_ciclo, dados.data))
    if resultado:
        raise erro_de_cobertura(*resultado)

    salarios = datas_de_salario(db, usuario_id) if abre_ciclo else []
    # Só um salário posterior a todos os outros abre um ciclo novo (e gera os previstos).
    abre_ciclo_novo = abre_ciclo and (not salarios or dados.data > max(salarios))
    usado_antes = usado_no_ciclo(db, usuario_id, categoria, dados.data, hoje)

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
    if pelo_mes:
        # O mês não tem evento de abertura: garante os previstos do mês atual.
        gerar_previstos(db, usuario_id, ciclo_mensal(hoje, hoje, None), agora)
    db.flush()
    aviso = avaliar_aviso(
        categoria, usado_antes, usado_no_ciclo(db, usuario_id, categoria, dados.data, hoje)
    )
    db.commit()
    return lancamento, aviso


def editar_lancamento(
    db: Session,
    usuario_id: int,
    lancamento_id: int,
    dados: LancamentoPatch,
    agora: datetime,
    hoje: date,
) -> tuple[Lancamento, AvisoLimiteOut | None]:
    """Edita o lançamento; devolve também o aviso se a categoria de destino piorar de situação."""
    tipo_renda = travar_escritas(db, usuario_id)
    pelo_mes = ciclo_pelo_mes(tipo_renda)
    lancamento = obter_lancamento(db, usuario_id, lancamento_id)
    enviados = dados.model_fields_set
    if not enviados:
        return lancamento, None
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
    if _e_de_servico(lancamento, tipo_renda):
        mudancas = {
            "valor": dados.valor is not None and dados.valor != lancamento.valor,
            "status": dados.status is not None and dados.status != lancamento.status,
            "categoria_id": muda_categoria,
            "data": dados.data is not None and dados.data != lancamento.data,
        }
        for campo, muda in mudancas.items():
            if muda:
                raise ErroApi(
                    422, "validacao", MENSAGEM_VALIDACAO, campos={campo: "Altere pelo serviço."}
                )
    if _e_deposito_de_cartela(db, lancamento.id):
        mudancas = {
            "valor": dados.valor is not None and dados.valor != lancamento.valor,
            "status": dados.status is not None and dados.status != lancamento.status,
            "categoria_id": muda_categoria,
        }
        for campo, muda in mudancas.items():
            if muda:
                raise ErroApi(
                    422,
                    "validacao",
                    MENSAGEM_VALIDACAO,
                    campos={campo: "Desmarque o depósito na cartela para mudar isto."},
                )

    categoria = (
        obter_categoria_ativa(db, usuario_id, dados.categoria_id)
        if "categoria_id" in enviados and dados.categoria_id is not None
        else lancamento.categoria
    )
    data = dados.data if dados.data is not None else lancamento.data
    status = dados.status if dados.status is not None else lancamento.status
    if not pelo_mes:
        _validar_salario(categoria, status, data, hoje)

    era_salario = lancamento.abre_ciclo
    sera_salario = not pelo_mes and categoria.e_salario and status == STATUS_REALIZADO
    resultado = _problema_depois_da_mudanca(db, usuario_id, lancamento.id, (sera_salario, data))
    if resultado:
        if era_salario or sera_salario:
            raise _erro_sem_ciclo()
        raise erro_de_cobertura(*resultado)

    # Uso da categoria de destino no ciclo da nova data, antes da mudança.
    usado_antes = usado_no_ciclo(db, usuario_id, categoria, data, hoje)
    lancamento.categoria = categoria
    lancamento.tipo = categoria.tipo
    lancamento.data = data
    lancamento.status = status
    if dados.valor is not None:
        lancamento.valor = dados.valor
    if "descricao" in enviados:
        lancamento.descricao = dados.descricao
    lancamento.atualizado_em = agora
    db.flush()
    aviso = avaliar_aviso(
        categoria, usado_antes, usado_no_ciclo(db, usuario_id, categoria, data, hoje)
    )
    db.commit()
    return lancamento, aviso


def excluir_lancamento(db: Session, usuario_id: int, lancamento_id: int) -> None:
    tipo_renda = travar_escritas(db, usuario_id)
    lancamento = obter_lancamento(db, usuario_id, lancamento_id)
    if _e_de_servico(lancamento, tipo_renda):
        raise ErroApi(
            409, "lancamento_de_servico", "Esta entrada é de um serviço: altere pelo serviço."
        )
    if lancamento.divida_id is not None:
        raise ErroApi(409, "parcela_de_divida", "Parcelas de dívida não podem ser excluídas.")
    if _e_deposito_de_cartela(db, lancamento.id):
        raise ErroApi(409, "deposito_de_cartela", "Desmarque o depósito na cartela para removê-lo.")
    if _problema_depois_da_mudanca(db, usuario_id, lancamento.id, None):
        raise _erro_sem_ciclo()
    db.delete(lancamento)
    db.commit()
