from pydantic import BaseModel


class ErroDetalhe(BaseModel):
    codigo: str
    mensagem: str
    campos: dict[str, str] | None = None


class ErroOut(BaseModel):
    erro: ErroDetalhe
