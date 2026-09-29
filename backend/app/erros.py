import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

MENSAGEM_VALIDACAO = "Dados inválidos."


class ErroApi(Exception):
    """Erro de negócio convertido para o formato único da API."""

    def __init__(
        self,
        status: int,
        codigo: str,
        mensagem: str,
        campos: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(mensagem)
        self.status = status
        self.codigo = codigo
        self.mensagem = mensagem
        self.campos = campos
        self.headers = headers


def resposta_erro(
    status: int,
    codigo: str,
    mensagem: str,
    campos: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    corpo = {"erro": {"codigo": codigo, "mensagem": mensagem, "campos": campos}}
    return JSONResponse(status_code=status, content=corpo, headers=headers)


def _mensagem_campo(erro: dict[str, Any]) -> str:
    tipo = erro["type"]
    ctx = erro.get("ctx") or {}
    if tipo == "missing":
        return "Campo obrigatório."
    if tipo == "extra_forbidden":
        return "Campo não permitido."
    if tipo == "value_error" and "error" in ctx:
        return str(ctx["error"])
    if tipo.startswith("date"):
        return "Data inválida."
    return "Valor inválido."


def _campos_validacao(exc: RequestValidationError) -> dict[str, str]:
    campos: dict[str, str] = {}
    for erro in exc.errors():
        nomes = [str(parte) for parte in erro["loc"] if parte not in ("body", "path", "query")]
        campo = ".".join(nomes) or "body"
        campos.setdefault(campo, _mensagem_campo(erro))
    return campos


async def _tratar_erro_api(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, ErroApi)
    return resposta_erro(exc.status, exc.codigo, exc.mensagem, exc.campos, exc.headers)


async def _tratar_validacao(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    return resposta_erro(422, "validacao", MENSAGEM_VALIDACAO, _campos_validacao(exc))


async def _tratar_http(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, StarletteHTTPException)
    if exc.status_code == 404:
        return resposta_erro(404, "nao_encontrado", "Recurso não encontrado.")
    return resposta_erro(exc.status_code, f"http_{exc.status_code}", str(exc.detail))


async def _tratar_inesperado(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Erro não tratado em %s %s", request.method, request.url.path)
    return resposta_erro(500, "erro_interno", "Erro interno. Tente novamente.")


def registrar_tratadores(app: FastAPI) -> None:
    app.add_exception_handler(ErroApi, _tratar_erro_api)
    app.add_exception_handler(RequestValidationError, _tratar_validacao)
    app.add_exception_handler(StarletteHTTPException, _tratar_http)
    app.add_exception_handler(Exception, _tratar_inesperado)
