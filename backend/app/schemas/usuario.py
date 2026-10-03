from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

from app.domain.usuario import (
    MAX_CARGO,
    MAX_NOME,
    TIPO_CLT,
    limpar_texto,
    normalizar_email,
    normalizar_telefone,
    validar_senha,
)

# A data de nascimento depende de "hoje"; ela é validada no serviço, com o relógio injetado.

TipoRenda = Literal["clt", "prestador", "clt_prestador"]


class DadosPessoaisIn(BaseModel):
    """Campos obrigatórios de toda conta, com as regras do cadastro."""

    model_config = ConfigDict(extra="forbid")

    nome: str
    email: str
    telefone: str
    cargo: str

    @field_validator("nome")
    @classmethod
    def _nome(cls, valor: str) -> str:
        return limpar_texto(valor, MAX_NOME)

    @field_validator("cargo")
    @classmethod
    def _cargo(cls, valor: str) -> str:
        return limpar_texto(valor, MAX_CARGO)

    @field_validator("email")
    @classmethod
    def _email(cls, valor: str) -> str:
        return normalizar_email(valor)

    @field_validator("telefone")
    @classmethod
    def _telefone(cls, valor: str) -> str:
        return normalizar_telefone(valor)


class CadastroIn(DadosPessoaisIn):
    senha: str
    data_nascimento: date | None = None
    tipo_renda: TipoRenda = TIPO_CLT

    @field_validator("senha")
    @classmethod
    def _senha(cls, valor: str) -> str:
        return validar_senha(valor)


class LoginIn(BaseModel):
    """Sem validação de formato: qualquer erro vira a mesma resposta genérica."""

    model_config = ConfigDict(extra="forbid")

    email: str
    senha: str


class TrocaSenhaIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    senha_atual: str
    nova_senha: str

    @field_validator("nova_senha")
    @classmethod
    def _nova_senha(cls, valor: str) -> str:
        return validar_senha(valor)


class PerfilIn(BaseModel):
    """Edição parcial: só os campos enviados mudam; `data_nascimento: null` remove a data.

    Nome, telefone e cargo não podem ser apagados (null é recusado). O e-mail não é editável.
    """

    model_config = ConfigDict(extra="forbid")

    nome: str | None = None
    telefone: str | None = None
    cargo: str | None = None
    data_nascimento: date | None = None
    # A troca é validada no serviço: não pode deixar lançamentos fora de ciclo.
    tipo_renda: TipoRenda | None = None
    # Carteira PJ ("Tenho CNPJ"); validada no serviço junto com o tipo de renda.
    tem_pj: bool | None = None

    @field_validator("nome")
    @classmethod
    def _nome(cls, valor: str | None) -> str:
        return limpar_texto(_obrigatorio(valor), MAX_NOME)

    @field_validator("tipo_renda", "tem_pj")
    @classmethod
    def _sem_null(cls, valor: object) -> object:
        if valor is None:
            raise ValueError("Campo obrigatório.")
        return valor

    @field_validator("cargo")
    @classmethod
    def _cargo(cls, valor: str | None) -> str:
        return limpar_texto(_obrigatorio(valor), MAX_CARGO)

    @field_validator("telefone")
    @classmethod
    def _telefone(cls, valor: str | None) -> str:
        return normalizar_telefone(_obrigatorio(valor))


def _obrigatorio(valor: str | None) -> str:
    # Validadores só rodam para campos enviados; null explícito chega aqui como None.
    if valor is None:
        raise ValueError("Campo obrigatório.")
    return valor


class UsuarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    email: str
    telefone: str
    cargo: str
    data_nascimento: date | None
    troca_senha_obrigatoria: bool
    # Só o papel do próprio usuário; serve para o frontend separar a área do administrador.
    papel: Literal["usuario", "admin"]
    tipo_renda: TipoRenda
    tem_pj: bool
    criado_em: datetime
