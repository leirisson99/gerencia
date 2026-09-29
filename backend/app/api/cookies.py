from fastapi import Response

from app.config import Settings

NOME_COOKIE_SESSAO = "sessao"


def definir_cookie_sessao(response: Response, token: str, settings: Settings) -> None:
    response.set_cookie(
        NOME_COOKIE_SESSAO,
        token,
        max_age=settings.sessao_dias_inatividade * 24 * 60 * 60,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )


def apagar_cookie_sessao(response: Response, settings: Settings) -> None:
    response.delete_cookie(
        NOME_COOKIE_SESSAO,
        path="/",
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
    )
