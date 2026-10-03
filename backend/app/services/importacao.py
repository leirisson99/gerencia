"""Importação de extrato: prévia (nada é gravado) e confirmação do lote (tudo ou nada)."""

import base64
import binascii
from collections import Counter
from datetime import date, datetime

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.extrato import ErroExtrato, LinhaExtrato
from app.domain.extrato.bancos import BANCOS, Banco
from app.domain.extrato.csv import MapeamentoCsv, ler_csv_generico
from app.domain.extrato.valores import decodificar
from app.domain.importacao import (
    classificar,
    cobertura_do_lote,
    ids_externos,
    normalizar_descricao,
    novo_ciclo_aberto,
    sugerir_categoria,
    tipo_da_linha,
)
from app.domain.usuario import ciclo_pelo_mes
from app.erros import MENSAGEM_VALIDACAO, ErroApi
from app.models import Categoria, Lancamento
from app.models.lancamento import STATUS_REALIZADO
from app.schemas.importacao import (
    MAX_BYTES_EXTRATO,
    MAX_LINHAS_EXTRATO,
    BancoOut,
    ImportacaoIn,
    ImportacaoOut,
    LinhaPreviaOut,
    PreviaIn,
    PreviaOut,
    ResumoPreviaOut,
)
from app.schemas.lancamento import MAX_DESCRICAO
from app.services.ciclo import datas_de_salario, tipo_renda_do_usuario, travar_escritas
from app.services.evento_uso import registrar
from app.services.lancamento import erro_de_cobertura, menor_data_dos_outros
from app.services.pdf import PdfSemTexto, linhas_do_pdf
from app.services.recorrencia import gerar_previstos


def listar_bancos() -> list[BancoOut]:
    """Bancos por nome e "Outro banco" por último."""
    bancos = sorted(BANCOS.values(), key=lambda b: (b.codigo == "outro", b.nome))
    return [BancoOut(codigo=b.codigo, nome=b.nome, formatos=b.formatos) for b in bancos]


def _erro_campo(campo: str, mensagem: str, codigo: str = "validacao") -> ErroApi:
    return ErroApi(422, codigo, MENSAGEM_VALIDACAO, campos={campo: mensagem})


def _banco(dados: PreviaIn) -> Banco:
    banco = BANCOS.get(dados.banco)
    if banco is None:
        raise _erro_campo("banco", "Banco não suportado.")
    if dados.formato not in banco.formatos:
        raise ErroApi(
            422,
            "formato_indisponivel",
            f"O {banco.nome} não tem leitura em {dados.formato.upper()}.",
            campos={"formato": "Formato indisponível para este banco."},
        )
    if (dados.formato == "csv_generico") != (dados.mapeamento is not None):
        mensagem = (
            "Informe as colunas do CSV."
            if dados.formato == "csv_generico"
            else "Só o CSV genérico usa mapeamento de colunas."
        )
        raise _erro_campo("mapeamento", mensagem)
    return banco


def _conteudo(arquivo_base64: str) -> bytes:
    try:
        conteudo = base64.b64decode(arquivo_base64, validate=True)
    except (binascii.Error, ValueError) as erro:
        raise ErroApi(422, "extrato_invalido", "O arquivo enviado está corrompido.") from erro
    if len(conteudo) > MAX_BYTES_EXTRATO:
        raise ErroApi(
            413, "extrato_grande", "O arquivo passa de 2 MB. Divida o período em mais extratos."
        )
    return conteudo


def _ler(banco: Banco, dados: PreviaIn, conteudo: bytes) -> list[LinhaExtrato]:
    try:
        if dados.formato == "pdf":
            assert banco.pdf is not None
            return banco.pdf(linhas_do_pdf(conteudo))
        texto = decodificar(conteudo)
        if dados.formato == "csv_generico":
            assert dados.mapeamento is not None
            return ler_csv_generico(texto, MapeamentoCsv(**dados.mapeamento.model_dump()))
        return banco.texto[dados.formato](texto)
    except PdfSemTexto as erro:
        raise ErroApi(422, "pdf_sem_texto", str(erro)) from erro
    except ErroExtrato as erro:
        raise ErroApi(422, "extrato_invalido", str(erro)) from erro


def _historico_de_categorias(db: Session, usuario_id: int) -> dict[str, tuple[int, str]]:
    """Descrição normalizada → (categoria, tipo) do lançamento mais recente, em categoria ativa."""
    consulta = (
        select(Lancamento.descricao, Categoria.id, Categoria.tipo)
        .join(Categoria, Lancamento.categoria_id == Categoria.id)
        .where(
            Lancamento.usuario_id == usuario_id,
            Lancamento.carteira == "pf",  # a importação grava na PF (fase 1 da 019)
            Lancamento.descricao.is_not(None),
            Categoria.ativa,
        )
        .order_by(Lancamento.data.desc(), Lancamento.id.desc())
    )
    historico: dict[str, tuple[int, str]] = {}
    for descricao, categoria_id, tipo in db.execute(consulta):
        historico.setdefault(normalizar_descricao(descricao), (categoria_id, tipo))
    return historico


def _existentes(
    db: Session, usuario_id: int, linhas: list[LinhaExtrato], ids: list[str]
) -> Counter[tuple[date, str, int]]:
    """Lançamentos PF do usuário no período do extrato, fora os já importados deste arquivo.

    A importação grava na PF; um lançamento da PJ não é duplicata do extrato pessoal.
    """
    datas = [linha.data for linha in linhas]
    consulta = select(Lancamento.data, Lancamento.tipo, Lancamento.valor).where(
        Lancamento.usuario_id == usuario_id,
        Lancamento.carteira == "pf",
        Lancamento.data >= min(datas),
        Lancamento.data <= max(datas),
        or_(Lancamento.id_externo.is_(None), Lancamento.id_externo.not_in(ids)),
    )
    return Counter((data, tipo, valor) for data, tipo, valor in db.execute(consulta))


def _ja_importados(db: Session, usuario_id: int, ids: list[str]) -> set[str]:
    return set(
        db.scalars(
            select(Lancamento.id_externo).where(
                Lancamento.usuario_id == usuario_id, Lancamento.id_externo.in_(ids)
            )
        )
    )


def previa(db: Session, usuario_id: int, dados: PreviaIn) -> PreviaOut:
    banco = _banco(dados)
    linhas = _ler(banco, dados, _conteudo(dados.arquivo_base64))
    if len(linhas) > MAX_LINHAS_EXTRATO:
        raise ErroApi(413, "extrato_grande", "O extrato passa de 5.000 linhas. Divida o período.")
    if not linhas:
        return PreviaOut(linhas=[], resumo=ResumoPreviaOut())

    ids = ids_externos(banco.codigo, dados.formato, linhas)
    # No ciclo pelo mês (prestador), nenhuma linha fica antes do primeiro ciclo.
    pelo_mes = ciclo_pelo_mes(tipo_renda_do_usuario(db, usuario_id))
    salarios = [] if pelo_mes else datas_de_salario(db, usuario_id)
    situacoes = classificar(
        linhas,
        ids,
        _ja_importados(db, usuario_id, ids),
        _existentes(db, usuario_id, linhas, ids),
        min(salarios) if salarios else None,
    )
    historico = _historico_de_categorias(db, usuario_id)

    saida = []
    for linha, id_externo, situacao in zip(linhas, ids, situacoes, strict=True):
        tipo = tipo_da_linha(linha.valor)
        saida.append(
            LinhaPreviaOut(
                id_externo=id_externo,
                data=linha.data,
                valor=abs(linha.valor),
                tipo=tipo,
                descricao=linha.descricao[:MAX_DESCRICAO].strip() or None,
                categoria_sugerida_id=sugerir_categoria(linha.descricao, tipo, historico),
                situacao=situacao,
            )
        )
    saida.sort(key=lambda linha: linha.data)  # estável: no mesmo dia, a ordem do arquivo
    return PreviaOut(linhas=saida, resumo=ResumoPreviaOut(**Counter(situacoes)))


def _categorias_das_linhas(
    db: Session, usuario_id: int, dados: ImportacaoIn
) -> dict[int, Categoria]:
    pedidas = {linha.categoria_id for linha in dados.linhas}
    categorias = {
        c.id: c
        for c in db.scalars(
            select(Categoria).where(Categoria.usuario_id == usuario_id, Categoria.id.in_(pedidas))
        )
    }
    if pedidas - categorias.keys():
        raise ErroApi(404, "nao_encontrado", "Categoria não encontrada.")
    return categorias


def _validar_linhas(
    dados: ImportacaoIn, categorias: dict[int, Categoria], hoje: date, pelo_mes: bool
) -> None:
    erros: dict[str, str] = {}
    for i, linha in enumerate(dados.linhas):
        categoria = categorias[linha.categoria_id]
        if not categoria.ativa:
            erros[f"linhas.{i}.categoria_id"] = "Categoria inativa."
        elif categoria.tipo != linha.tipo:
            erros[f"linhas.{i}.categoria_id"] = (
                "A linha é de entrada; escolha uma categoria de entrada."
                if linha.tipo == "entrada"
                else "A linha é de saída; escolha uma categoria de saída."
            )
        elif not pelo_mes and categoria.e_salario and linha.data > hoje:
            erros[f"linhas.{i}.data"] = (
                "O salário é lançado quando entra; a data não pode ser futura."
            )
    if erros:
        raise ErroApi(422, "validacao", MENSAGEM_VALIDACAO, campos=erros)


def confirmar(
    db: Session, usuario_id: int, dados: ImportacaoIn, agora: datetime, hoje: date
) -> ImportacaoOut:
    pelo_mes = ciclo_pelo_mes(travar_escritas(db, usuario_id))
    categorias = _categorias_das_linhas(db, usuario_id, dados)
    _validar_linhas(dados, categorias, hoje, pelo_mes)

    ja_importados = _ja_importados(db, usuario_id, [linha.id_externo for linha in dados.linhas])
    novas = []
    for linha in dados.linhas:
        if linha.id_externo not in ja_importados:
            ja_importados.add(linha.id_externo)  # repetida no próprio lote conta uma vez
            novas.append(linha)

    # Para o prestador, "Salário" não abre ciclo e não há cobertura a verificar.
    salarios = [] if pelo_mes else datas_de_salario(db, usuario_id)
    salarios_lote = (
        []
        if pelo_mes
        else [linha.data for linha in novas if categorias[linha.categoria_id].e_salario]
    )
    if not pelo_mes:
        problema = cobertura_do_lote(
            salarios,
            menor_data_dos_outros(db, usuario_id, None),
            [(categorias[linha.categoria_id].e_salario, linha.data) for linha in novas],
        )
        if problema:
            raise erro_de_cobertura(problema, salarios + salarios_lote)

    lancamentos = [
        Lancamento(
            usuario_id=usuario_id,
            categoria_id=linha.categoria_id,
            data=linha.data,
            valor=linha.valor,
            tipo=categorias[linha.categoria_id].tipo,
            descricao=linha.descricao,
            status=STATUS_REALIZADO,
            id_externo=linha.id_externo,
            criado_em=agora,
            atualizado_em=agora,
        )
        for linha in novas
    ]
    registrar(db, usuario_id, "extrato_importado")
    db.add_all(lancamentos)
    if ciclo := novo_ciclo_aberto(salarios, salarios_lote):
        gerar_previstos(db, usuario_id, ciclo, agora)
    try:
        db.flush()
        db.commit()
    except IntegrityError as erro:
        db.rollback()
        raise ErroApi(
            409, "conflito_importacao", "Essas linhas acabaram de ser importadas. Refaça a prévia."
        ) from erro
    return ImportacaoOut(
        criados=len(lancamentos),
        ignoradas=len(dados.linhas) - len(novas),
        lancamento_ids=[lancamento.id for lancamento in lancamentos],
    )
