from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

CONVENCAO_NOMES = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=CONVENCAO_NOMES)


from app.models.categoria import Categoria  # noqa: E402
from app.models.lancamento import Lancamento  # noqa: E402
from app.models.sessao import Sessao  # noqa: E402
from app.models.tentativa_login import TentativaLogin  # noqa: E402
from app.models.usuario import Usuario  # noqa: E402

__all__ = ["Base", "Categoria", "Lancamento", "Sessao", "TentativaLogin", "Usuario"]
