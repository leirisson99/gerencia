from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.categoria import CATEGORIAS_INICIAIS
from app.erros import MENSAGEM_VALIDACAO, ErroApi
from app.models import Categoria


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


def listar_categorias(db: Session, usuario_id: int) -> list[Categoria]:
    """Ativas; "Salário" primeiro, depois entradas e saídas por nome."""
    categorias = db.scalars(
        select(Categoria).where(Categoria.usuario_id == usuario_id, Categoria.ativa)
    ).all()
    return sorted(categorias, key=lambda c: (not c.e_salario, c.tipo != "entrada", c.nome))


def obter_categoria_ativa(db: Session, usuario_id: int, categoria_id: int) -> Categoria:
    """Categoria do usuário; a de outro usuário responde como inexistente."""
    categoria = db.scalar(
        select(Categoria).where(Categoria.id == categoria_id, Categoria.usuario_id == usuario_id)
    )
    if categoria is None:
        raise ErroApi(404, "nao_encontrado", "Categoria não encontrada.")
    if not categoria.ativa:
        raise ErroApi(
            422, "validacao", MENSAGEM_VALIDACAO, campos={"categoria_id": "Categoria inativa."}
        )
    return categoria
