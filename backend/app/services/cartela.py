from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.cartela import gerar_casas, progresso, quantidade_de_casas
from app.domain.categoria import NOME_POUPANCA
from app.erros import MENSAGEM_VALIDACAO, ErroApi
from app.models import Cartela, Casa, Categoria, Lancamento
from app.models.lancamento import STATUS_REALIZADO
from app.schemas.cartela import CartelaIn, CartelaOut, CasaOut
from app.services.ciclo import travar_escritas
from app.services.lancamento import verificar_novos_lancamentos

MAX_CASAS = 1_000


def _erro_meta(mensagem: str) -> ErroApi:
    return ErroApi(422, "validacao", MENSAGEM_VALIDACAO, campos={"meta": mensagem})


def criar_cartela(db: Session, usuario_id: int, dados: CartelaIn, agora: datetime) -> CartelaOut:
    try:
        # Conta antes de gerar: metas enormes com base pequena teriam milhares de casas.
        quantidade = quantidade_de_casas(dados.meta, dados.valor_base)
    except ValueError as erro:
        raise _erro_meta(str(erro)) from None
    if quantidade > MAX_CASAS:
        raise _erro_meta(f"A cartela teria mais de {MAX_CASAS} casas; aumente o valor base.")

    cartela = Cartela(
        usuario_id=usuario_id,
        nome=dados.nome,
        meta=dados.meta,
        valor_base=dados.valor_base,
        criada_em=agora,
    )
    db.add(cartela)
    db.flush()
    for casa in gerar_casas(dados.meta, dados.valor_base):
        db.add(
            Casa(
                cartela_id=cartela.id,
                valor=casa.valor,
                ordem=casa.ordem,
                is_ajuste=casa.is_ajuste,
            )
        )
    db.commit()
    return _saida(db, cartela)


def _casas(db: Session, cartela_id: int) -> list[Casa]:
    return list(db.scalars(select(Casa).where(Casa.cartela_id == cartela_id).order_by(Casa.ordem)))


def _saida(db: Session, cartela: Cartela) -> CartelaOut:
    casas = _casas(db, cartela.id)
    atual = progresso(((c.valor, c.depositado_em is not None) for c in casas), cartela.meta)
    return CartelaOut(
        id=cartela.id,
        nome=cartela.nome,
        meta=cartela.meta,
        valor_base=cartela.valor_base,
        guardado=atual.guardado,
        falta=atual.falta,
        percentual=atual.percentual,
        maior_casa_livre=atual.maior_casa_livre,
        casas=[CasaOut.model_validate(c) for c in casas],
    )


def _obter(db: Session, usuario_id: int, cartela_id: int) -> Cartela:
    cartela = db.scalar(
        select(Cartela).where(Cartela.id == cartela_id, Cartela.usuario_id == usuario_id)
    )
    if cartela is None:
        raise ErroApi(404, "nao_encontrado", "Cartela não encontrada.")
    return cartela


def _obter_casa(db: Session, cartela: Cartela, casa_id: int) -> Casa:
    casa = db.scalar(select(Casa).where(Casa.id == casa_id, Casa.cartela_id == cartela.id))
    if casa is None:
        raise ErroApi(404, "nao_encontrado", "Casa não encontrada.")
    return casa


def listar_cartelas(db: Session, usuario_id: int) -> list[CartelaOut]:
    cartelas = db.scalars(
        select(Cartela).where(Cartela.usuario_id == usuario_id).order_by(Cartela.id)
    )
    return [_saida(db, cartela) for cartela in cartelas]


def obter_cartela(db: Session, usuario_id: int, cartela_id: int) -> CartelaOut:
    return _saida(db, _obter(db, usuario_id, cartela_id))


def depositar(
    db: Session, usuario_id: int, cartela_id: int, casa_id: int, agora: datetime, hoje: date
) -> CartelaOut:
    """Marca a casa e lança a saída na categoria de sistema Poupança, numa transação.

    O dinheiro guardado continua do usuário: a saída não conta no saldo nem como gasto.
    """
    travar_escritas(db, usuario_id)
    cartela = _obter(db, usuario_id, cartela_id)
    casa = _obter_casa(db, cartela, casa_id)
    if casa.depositado_em is not None:
        raise ErroApi(409, "casa_depositada", "Esta casa já foi depositada.")
    verificar_novos_lancamentos(db, usuario_id, hoje)

    poupanca = db.scalar(
        select(Categoria).where(
            Categoria.usuario_id == usuario_id,
            Categoria.sistema,
            Categoria.nome == NOME_POUPANCA,
        )
    )
    assert poupanca is not None, "todo usuário tem a categoria de sistema Poupança"
    lancamento = Lancamento(
        usuario_id=usuario_id,
        categoria_id=poupanca.id,
        data=hoje,
        valor=casa.valor,
        tipo=poupanca.tipo,
        descricao=f"Cartela {cartela.nome}",
        status=STATUS_REALIZADO,
        conta_no_saldo=False,
        criado_em=agora,
        atualizado_em=agora,
    )
    db.add(lancamento)
    db.flush()
    casa.depositado_em = hoje
    casa.lancamento_id = lancamento.id
    db.commit()
    return _saida(db, cartela)


def desfazer_deposito(db: Session, usuario_id: int, cartela_id: int, casa_id: int) -> CartelaOut:
    travar_escritas(db, usuario_id)
    cartela = _obter(db, usuario_id, cartela_id)
    casa = _obter_casa(db, cartela, casa_id)
    if casa.lancamento_id is None:
        raise ErroApi(409, "casa_livre", "Esta casa ainda não foi depositada.")
    lancamento = db.get(Lancamento, casa.lancamento_id)
    casa.depositado_em = None
    casa.lancamento_id = None
    db.flush()
    db.delete(lancamento)
    db.commit()
    return _saida(db, cartela)
