from datetime import date

from pydantic import BaseModel, ConfigDict


class CicloOut(BaseModel):
    """`fim` é null no ciclo aberto; `anterior`/`proximo` são os inícios dos vizinhos."""

    model_config = ConfigDict(from_attributes=True)

    inicio: date
    fim: date | None
    aberto: bool
    anterior: date | None
    proximo: date | None


class SugestaoSalarioOut(BaseModel):
    valor: int | None
