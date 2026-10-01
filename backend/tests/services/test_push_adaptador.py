"""Adaptador do pywebpush: traduz a resposta do serviço de push, sem rede."""

from typing import Any

import pytest
import requests
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from py_vapid import Vapid
from py_vapid.utils import b64urlencode
from pywebpush import WebPushException

from app import push
from app.models import InscricaoPush


@pytest.fixture
def chave_privada() -> str:
    vapid = Vapid()
    vapid.generate_keys()
    return b64urlencode(vapid.private_key.private_numbers().private_value.to_bytes(32, "big"))


@pytest.fixture
def inscricao() -> InscricaoPush:
    return InscricaoPush(
        usuario_id=1, endpoint="https://push.exemplo/ana-1", p256dh="p" * 87, auth="a" * 22
    )


def _resposta(status: int) -> requests.Response:
    resposta = requests.Response()
    resposta.status_code = status
    return resposta


def test_envia_payload_com_vapid_ttl_e_urgencia(
    monkeypatch: pytest.MonkeyPatch, chave_privada: str, inscricao: InscricaoPush
) -> None:
    chamadas: list[dict[str, Any]] = []
    monkeypatch.setattr(push, "webpush", lambda **kw: chamadas.append(kw) or _resposta(201))
    enviador = push.EnviadorWebPush(chave_privada, "mailto:admin@exemplo.com")

    resultado = enviador.enviar(inscricao, {"titulo": "Gerencia", "corpo": "1 lembrete."})

    assert resultado == "ok"
    (chamada,) = chamadas
    assert chamada["subscription_info"] == {
        "endpoint": "https://push.exemplo/ana-1",
        "keys": {"p256dh": "p" * 87, "auth": "a" * 22},
    }
    assert chamada["data"] == '{"titulo": "Gerencia", "corpo": "1 lembrete."}'
    assert chamada["vapid_claims"] == {"sub": "mailto:admin@exemplo.com"}
    assert chamada["ttl"] == 43200
    assert chamada["headers"] == {"Urgency": "normal"}
    # A chave carregada corresponde à privada configurada.
    publica = Vapid.from_string(chave_privada).public_key.public_bytes(
        Encoding.X962, PublicFormat.UncompressedPoint
    )
    assert (
        chamada["vapid_private_key"].public_key.public_bytes(
            Encoding.X962, PublicFormat.UncompressedPoint
        )
        == publica
    )


@pytest.mark.parametrize(
    ("status", "resultado"), [(404, "expirado"), (410, "expirado"), (429, "falha"), (500, "falha")]
)
def test_traduz_recusa_do_servico(
    monkeypatch: pytest.MonkeyPatch,
    chave_privada: str,
    inscricao: InscricaoPush,
    status: int,
    resultado: str,
) -> None:
    def recusar(**_: Any) -> None:
        raise WebPushException("recusado", response=_resposta(status))

    monkeypatch.setattr(push, "webpush", recusar)

    assert push.EnviadorWebPush(chave_privada, "mailto:a@b.com").enviar(inscricao, {}) == resultado


def test_erro_de_rede_e_falha(
    monkeypatch: pytest.MonkeyPatch, chave_privada: str, inscricao: InscricaoPush
) -> None:
    def sem_rede(**_: Any) -> None:
        raise requests.ConnectionError("sem rede")

    monkeypatch.setattr(push, "webpush", sem_rede)

    assert push.EnviadorWebPush(chave_privada, "mailto:a@b.com").enviar(inscricao, {}) == "falha"


def test_claims_novos_a_cada_envio(
    monkeypatch: pytest.MonkeyPatch, chave_privada: str, inscricao: InscricaoPush
) -> None:
    # O pywebpush acrescenta aud/exp no dict recebido; um envio não pode herdar o do outro.
    vistos: list[dict[str, Any]] = []

    def enviar(**kw: Any) -> requests.Response:
        vistos.append(dict(kw["vapid_claims"]))
        kw["vapid_claims"]["aud"] = "https://push.exemplo"
        return _resposta(201)

    monkeypatch.setattr(push, "webpush", enviar)
    enviador = push.EnviadorWebPush(chave_privada, "mailto:a@b.com")
    enviador.enviar(inscricao, {})
    enviador.enviar(inscricao, {})

    assert vistos == [{"sub": "mailto:a@b.com"}, {"sub": "mailto:a@b.com"}]
