from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

SAO_PAULO = ZoneInfo("America/Sao_Paulo")


class Relogio:
    """Fonte única de hora da aplicação; substituída nos testes."""

    def agora_utc(self) -> datetime:
        return datetime.now(UTC)

    def hoje_sp(self) -> date:
        return self.agora_utc().astimezone(SAO_PAULO).date()


def get_relogio() -> Relogio:
    return Relogio()
