import logging
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    admin,
    auth,
    cartelas,
    categorias,
    ciclos,
    dividas,
    health,
    importacoes,
    lancamentos,
    me,
    recorrencias,
)
from app.config import Settings, get_settings
from app.erros import registrar_tratadores, resposta_erro

METODOS_COM_CORPO = {"POST", "PUT", "PATCH", "DELETE"}


def _tem_corpo(request: Request) -> bool:
    tamanho = request.headers.get("content-length")
    if tamanho is not None:
        return tamanho != "0"
    return "transfer-encoding" in request.headers


async def exigir_json(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Corpo só em JSON: formulários de outros sites não passam sem preflight de CORS."""
    if request.method in METODOS_COM_CORPO and _tem_corpo(request):
        tipo = request.headers.get("content-type", "")
        if not tipo.startswith("application/json"):
            return resposta_erro(415, "tipo_conteudo_invalido", "Envie o corpo como JSON.")
    return await call_next(request)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    # Só o nível: nunca registrar corpo, cookies ou dados pessoais.
    logging.basicConfig(level=settings.log_level)

    app = FastAPI(title="Gerencia API", version="0.1.0")
    registrar_tratadores(app)
    app.middleware("http")(exigir_json)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Content-Type"],
    )
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(me.router)
    app.include_router(categorias.router)
    app.include_router(lancamentos.router)
    app.include_router(ciclos.router)
    app.include_router(recorrencias.router)
    app.include_router(dividas.router)
    app.include_router(cartelas.router)
    app.include_router(importacoes.router)
    app.include_router(admin.router)
    return app


app = create_app()
