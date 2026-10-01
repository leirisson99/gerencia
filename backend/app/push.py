"""Transporte Web Push (VAPID) com o pywebpush. Infraestrutura: a regra do envio fica em
services/envio_lembrete.py.

Nunca registra endpoint, chaves nem payload em log.
"""

import json
from typing import Any

import requests
from py_vapid import Vapid
from pywebpush import WebPushException, webpush

from app.models import InscricaoPush
from app.services.envio_lembrete import ResultadoEnvio

TTL_SEGUNDOS = 12 * 60 * 60  # o resumo do dia perde o sentido depois disso
EXPIRADO = {404, 410}  # o aparelho revogou ou a inscrição expirou: não adianta tentar de novo


class EnviadorWebPush:
    def __init__(self, chave_privada: str, contato: str) -> None:
        self._vapid = Vapid.from_string(chave_privada)
        self._contato = contato

    def enviar(self, inscricao: InscricaoPush, payload: dict[str, Any]) -> ResultadoEnvio:
        try:
            webpush(
                subscription_info={
                    "endpoint": inscricao.endpoint,
                    "keys": {"p256dh": inscricao.p256dh, "auth": inscricao.auth},
                },
                data=json.dumps(payload, ensure_ascii=False),
                vapid_private_key=self._vapid,
                # Dict novo a cada envio: o pywebpush acrescenta aud e exp nele.
                vapid_claims={"sub": self._contato},
                ttl=TTL_SEGUNDOS,
                headers={"Urgency": "normal"},
            )
        except WebPushException as erro:
            status = erro.response.status_code if erro.response is not None else None
            return "expirado" if status in EXPIRADO else "falha"
        except requests.RequestException:
            return "falha"
        return "ok"
