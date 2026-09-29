from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.categoria import CATEGORIAS_INICIAIS, edicao_permitida
from app.erros import MENSAGEM_VALIDACAO, ErroApi
from app.models import Categoria
from app.schemas.categoria import CategoriaIn, CategoriaPatch


def criar_categorias_iniciais(db: Session, usuario_id: int) -> None:
    for inicial in CATEGORIAS_INICIAIS:
        db.add(
            Categoria(
                usuario_id=usuario_id,
                nome=inicial.nome,
                tipo=inicial.tipo,
                sistema=inicial.sistema,
            )
        )


def listar_categorias(
    db: Session, usuario_id: int, incluir_inativas: bool = False
) -> list[Categoria]:
    """Ordem: Salário, depois entradas e saídas por nome."""
    consulta = select(Categoria).where(Categoria.usuario_id == usuario_id)
    if not incluir_inativas:
        consulta = consulta.where(Categoria.ativa)
    categorias = db.scalars(consulta).all()
    return sorted(categorias, key=lambda c: (not c.e_salario, c.tipo != "entrada", c.nome))


def obter_categoria(db: Session, usuario_id: int, categoria_id: int) -> Categoria:
    """Categoria do usuário; a de outro usuário responde como inexistente."""
    categoria = db.scalar(
        select(Categoria).where(Categoria.id == categoria_id, Categoria.usuario_id == usuario_id)
    )
    if categoria is None:
        raise ErroApi(404, "nao_encontrado", "Categoria não encontrada.")
    return categoria


def obter_categoria_ativa(db: Session, usuario_id: int, categoria_id: int) -> Categoria:
    categoria = obter_categoria(db, usuario_id, categoria_id)
    if not categoria.ativa:
        raise ErroApi(
            422, "validacao", MENSAGEM_VALIDACAO, campos={"categoria_id": "Categoria inativa."}
        )
    return categoria


def _gravar(db: Session) -> None:
    """Grava; nome repetido (índice único, também em requisições simultâneas) vira 409."""
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ErroApi(
            409, "categoria_existente", "Já existe uma categoria com esse nome."
        ) from None


def criar_categoria(db: Session, usuario_id: int, dados: CategoriaIn) -> Categoria:
    categoria = Categoria(usuario_id=usuario_id, nome=dados.nome, tipo=dados.tipo)
    db.add(categoria)
    _gravar(db)
    return categoria


def editar_categoria(
    db: Session, usuario_id: int, categoria_id: int, dados: CategoriaPatch
) -> Categoria:
    categoria = obter_categoria(db, usuario_id, categoria_id)
    muda_nome = dados.nome is not None and dados.nome != categoria.nome
    desativa = dados.ativa is False and categoria.ativa
    if not edicao_permitida(categoria.sistema, muda_nome, desativa):
        raise ErroApi(409, "categoria_do_sistema", "Categorias do sistema não podem ser alteradas.")
    if dados.nome is not None:
        categoria.nome = dados.nome
    if dados.ativa is not None:
        categoria.ativa = dados.ativa
    _gravar(db)
    return categoria
