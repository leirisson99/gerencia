from datetime import date
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator, model_validator

from app.domain.extrato import Formato
from app.domain.importacao import MAX_ID_EXTERNO, Situacao, Tipo
from app.schemas.lancamento import Valor, limpar_descricao

MAX_BYTES_EXTRATO = 2 * 1024 * 1024  # 2 MB
MAX_LINHAS_EXTRATO = 5_000
# O limite em bytes é conferido depois de decodificar (413); aqui só barra o absurdo.
MAX_BASE64 = 3_000_000


class BancoOut(BaseModel):
    codigo: str
    nome: str
    formatos: list[Formato]


class MapeamentoCsvIn(BaseModel):
    """Colunas a partir de 0. Envie `coluna_valor` ou o par `coluna_credito` e `coluna_debito`."""

    model_config = ConfigDict(extra="forbid")

    separador: Literal[";", ",", "\t"]
    pular_linhas: int = Field(0, ge=0, le=50)
    tem_cabecalho: bool = True
    coluna_data: int = Field(ge=0, le=99)
    formato_data: Literal["dd/mm/aaaa", "dd-mm-aaaa", "aaaa-mm-dd", "mm/dd/aaaa"]
    coluna_descricao: int = Field(ge=0, le=99)
    coluna_valor: int | None = Field(None, ge=0, le=99)
    coluna_credito: int | None = Field(None, ge=0, le=99)
    coluna_debito: int | None = Field(None, ge=0, le=99)
    separador_decimal: Literal[",", "."]

    @model_validator(mode="after")
    def _uma_forma_de_valor(self) -> Self:
        par = (self.coluna_credito, self.coluna_debito)
        if self.coluna_valor is None and None in par:
            raise ValueError("Informe a coluna de valor ou as colunas de crédito e de débito.")
        if self.coluna_valor is not None and par != (None, None):
            raise ValueError("Use a coluna de valor ou crédito e débito, não os dois.")
        return self


class PreviaIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    banco: str = Field(min_length=1, max_length=30)
    formato: Formato
    arquivo_base64: str = Field(min_length=1, max_length=MAX_BASE64)
    mapeamento: MapeamentoCsvIn | None = None


class LinhaPreviaOut(BaseModel):
    id_externo: str
    data: date
    valor: int  # centavos, sempre positivo; o sinal está em `tipo`
    tipo: Tipo
    descricao: str | None
    categoria_sugerida_id: int | None
    situacao: Situacao


class ResumoPreviaOut(BaseModel):
    nova: int = 0
    ja_importada: int = 0
    possivel_duplicada: int = 0
    antes_do_primeiro_ciclo: int = 0
    invalida: int = 0


class PreviaOut(BaseModel):
    """Nada é gravado. Linhas por data e, no mesmo dia, na ordem do arquivo."""

    linhas: list[LinhaPreviaOut]
    resumo: ResumoPreviaOut


class LinhaImportacaoIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id_externo: str = Field(min_length=1, max_length=MAX_ID_EXTERNO)
    data: date
    valor: Valor
    tipo: Tipo
    descricao: str | None = None
    categoria_id: StrictInt

    @field_validator("descricao")
    @classmethod
    def _descricao(cls, valor: str | None) -> str | None:
        return limpar_descricao(valor)


class ImportacaoIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    linhas: list[LinhaImportacaoIn] = Field(min_length=1, max_length=MAX_LINHAS_EXTRATO)


class ImportacaoOut(BaseModel):
    """`ignoradas`: linhas já importadas antes ou repetidas no próprio lote."""

    criados: int
    ignoradas: int
    lancamento_ids: list[int]
