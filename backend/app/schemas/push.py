from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

MAX_ENDPOINT = 2048

Endpoint = Annotated[
    str, StringConstraints(strip_whitespace=True, pattern=r"^https://", max_length=MAX_ENDPOINT)
]


class ChavePushOut(BaseModel):
    """Chave pública VAPID: o navegador a usa como `applicationServerKey`."""

    chave_publica: str


class ChavesInscricao(BaseModel):
    model_config = ConfigDict(extra="forbid")

    p256dh: Annotated[str, Field(min_length=1, max_length=200)]
    auth: Annotated[str, Field(min_length=1, max_length=100)]


class InscricaoIn(BaseModel):
    """Formato de `PushSubscription.toJSON()`; `expirationTime` é aceito e ignorado."""

    model_config = ConfigDict(extra="forbid")

    endpoint: Endpoint
    keys: ChavesInscricao
    expiracao: int | None = Field(default=None, alias="expirationTime")


class InscricaoRemoverIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    endpoint: Annotated[str, Field(max_length=MAX_ENDPOINT)]
