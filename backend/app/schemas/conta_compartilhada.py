from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator

from app.domain.conta_compartilhada import Modo, StatusCota
from app.domain.usuario import limpar_texto, normalizar_email
from app.schemas.lancamento import MAX_DESCRICAO, Valor
from app.schemas.recorrencia import Dia

# Percentual em pontos-base (0 a 10000) ou centavos, conforme o modo da conta.
ValorDaParte = Annotated[StrictInt, Field(ge=0, le=10**12)]
StatusParticipante = Literal["pendente", "aceito", "recusado", "removido", "saiu"]


class ContaIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    descricao: str
    categoria_id: StrictInt
    modo: Modo
    dia_vencimento: Dia
    valor_fixo: Valor | None = None

    @field_validator("descricao")
    @classmethod
    def _descricao(cls, valor: str) -> str:
        return limpar_texto(valor, MAX_DESCRICAO)


class ContaPatch(BaseModel):
    """Só o que veio é alterado (`model_fields_set`); `valor_fixo: null` volta a ser variável."""

    model_config = ConfigDict(extra="forbid")

    descricao: str | None = None
    categoria_id: StrictInt | None = None
    modo: Modo | None = None
    dia_vencimento: Dia | None = None
    valor_fixo: Valor | None = None
    ativa: bool | None = None

    @field_validator("descricao")
    @classmethod
    def _descricao(cls, valor: str | None) -> str | None:
        return None if valor is None else limpar_texto(valor, MAX_DESCRICAO)


class ConviteIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str
    valor: ValorDaParte | None = None

    @field_validator("email")
    @classmethod
    def _email(cls, valor: str) -> str:
        return normalizar_email(valor)


class ParticipantePatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    valor: ValorDaParte | None


class AceiteIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    categoria_id: StrictInt


class CobrancaIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    competencia: date
    valor_total: Valor | None = None


class MinhaCotaOut(BaseModel):
    id: int
    valor: int
    status: StatusCota
    lancamento_id: int | None


class OutroParticipanteOut(BaseModel):
    """O que um participante vê dos demais: nome e status, nunca e-mail nem valor."""

    nome: str
    status: StatusCota


class ParticipanteDonoOut(BaseModel):
    id: int
    nome: str | None
    email_convite: str | None
    status: StatusParticipante
    expirado: bool  # convite pendente com mais de 30 dias
    eh_dono: bool
    valor: int | None
    cota_id: int | None
    cota: int | None
    status_cota: StatusCota | None


class ContaResumoOut(BaseModel):
    id: int
    descricao: str
    papel: Literal["dono", "participante"]
    ativa: bool
    dia_vencimento: int
    valor_total: int | None
    qtd_pessoas: int
    qtd_convidados_pendentes: int
    minha_cota: MinhaCotaOut | None
    falta_informar_total: bool


class ContaDonoOut(BaseModel):
    papel: Literal["dono"] = "dono"
    id: int
    descricao: str
    categoria_id: int
    modo: Modo
    dia_vencimento: int
    valor_fixo: int | None
    ativa: bool
    valor_total: int | None
    qtd_pessoas: int
    qtd_convidados_pendentes: int
    falta_informar_total: bool
    minha_cota: MinhaCotaOut | None
    participantes: list[ParticipanteDonoOut]


class ContaParticipanteOut(BaseModel):
    papel: Literal["participante"] = "participante"
    id: int
    descricao: str
    dia_vencimento: int
    ativa: bool
    valor_total: int | None
    qtd_pessoas: int
    qtd_convidados_pendentes: int
    minha_cota: MinhaCotaOut | None
    outros: list[OutroParticipanteOut]


class ConviteOut(BaseModel):
    id: int
    descricao_conta: str
    nome_do_dono: str
    convidado_em: datetime
