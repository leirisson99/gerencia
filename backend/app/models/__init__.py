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


from app.models.acao_admin import AcaoAdmin  # noqa: E402
from app.models.cartela import Cartela, Casa  # noqa: E402
from app.models.categoria import Categoria  # noqa: E402
from app.models.divida import Divida  # noqa: E402
from app.models.lancamento import Lancamento  # noqa: E402
from app.models.lembrete import EnvioLembrete, InscricaoPush, Lembrete  # noqa: E402
from app.models.recorrencia import Recorrencia  # noqa: E402
from app.models.servico import Servico  # noqa: E402
from app.models.sessao import Sessao  # noqa: E402
from app.models.tentativa_login import TentativaLogin  # noqa: E402
from app.models.usuario import Usuario  # noqa: E402

__all__ = [
    "AcaoAdmin",
    "Base",
    "Cartela",
    "Casa",
    "Categoria",
    "Divida",
    "EnvioLembrete",
    "InscricaoPush",
    "Lancamento",
    "Lembrete",
    "Recorrencia",
    "Servico",
    "Sessao",
    "TentativaLogin",
    "Usuario",
]
