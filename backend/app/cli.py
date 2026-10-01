"""Comandos de servidor.

Uso:
  uv run python -m app.cli hash-senha          # gera o ADMIN_SENHA_HASH do .env
  uv run python -m app.cli gerar-chaves-vapid  # gera as chaves do push (VAPID_*) do .env
  uv run python -m app.cli enviar-lembretes    # envia o resumo do dia (cron, 8h de São Paulo)
  uv run python -m app.cli testar-login EMAIL  # entra na API pedindo a senha (--api URL)
"""

import argparse
import json
import sys
from collections.abc import Callable
from getpass import getpass
from http.cookiejar import CookieJar
from typing import Any
from urllib.error import HTTPError
from urllib.request import HTTPCookieProcessor, Request, build_opener

from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from py_vapid import Vapid
from py_vapid.utils import b64urlencode

from app.config import get_settings
from app.db import SessionLocal
from app.domain.usuario import validar_senha
from app.relogio import Relogio
from app.services.envio_lembrete import enviar_lembretes_do_dia
from app.services.senha import hash_senha


def _hash_senha(_: argparse.Namespace) -> int:
    senha = getpass("Senha do administrador: ")
    if getpass("Repita a senha: ") != senha:
        print("As senhas não conferem.", file=sys.stderr)
        return 1
    try:
        validar_senha(senha)
    except ValueError as erro:
        print(erro, file=sys.stderr)
        return 1

    # Aspas simples: o .env não tenta expandir os "$" do hash.
    print("Copie a linha abaixo para o .env e reinicie a API:")
    print(f"ADMIN_SENHA_HASH='{hash_senha(senha)}'")
    return 0


def _gerar_chaves_vapid(_: argparse.Namespace) -> int:
    vapid = Vapid()
    vapid.generate_keys()
    privada = vapid.private_key.private_numbers().private_value.to_bytes(32, "big")
    publica = vapid.public_key.public_bytes(Encoding.X962, PublicFormat.UncompressedPoint)

    # Gere uma vez só: trocar as chaves invalida as notificações já ativadas nos aparelhos.
    print("Copie as linhas abaixo para o .env (a privada é segredo) e reinicie a API:")
    print(f"VAPID_CHAVE_PUBLICA={b64urlencode(publica)}")
    print(f"VAPID_CHAVE_PRIVADA={b64urlencode(privada)}")
    return 0


def _enviar_lembretes(_: argparse.Namespace) -> int:
    """Resumo do dia por push. A saída só tem contagens: nada de endpoints, valores ou textos."""
    from app.push import EnviadorWebPush

    settings = get_settings()
    if not (settings.vapid_chave_privada and settings.vapid_contato):
        print(
            "Push desligado: configure VAPID_CHAVE_PRIVADA e VAPID_CONTATO no .env.",
            file=sys.stderr,
        )
        return 1

    enviador = EnviadorWebPush(settings.vapid_chave_privada, settings.vapid_contato)
    with SessionLocal() as db:
        r = enviar_lembretes_do_dia(db, Relogio().hoje_sp(), enviador)
    print(
        f"usuarios={r.usuarios} enviados={r.enviados} sem_pendencias={r.sem_pendencias} "
        f"ja_enviados={r.ja_enviados} removidos={r.removidos} falhas={r.falhas}"
    )
    return 0


def _requisitar(
    abrir: Callable[..., Any], metodo: str, url: str, corpo: object = None
) -> tuple[int, dict[str, Any]]:
    """Chamada JSON à API; erros HTTP voltam como status, não como exceção."""
    dados = json.dumps(corpo).encode() if corpo is not None else None
    pedido = Request(url, data=dados, method=metodo, headers={"Content-Type": "application/json"})
    try:
        with abrir(pedido, timeout=10) as resposta:
            status, texto = resposta.status, resposta.read()
    except HTTPError as erro:
        status, texto = erro.code, erro.read()
    return status, json.loads(texto) if texto else {}


def _testar_login(args: argparse.Namespace) -> int:
    """Entra na API com e-mail e senha, como o frontend faz, e encerra a sessão no fim."""
    senha = getpass(f"Senha de {args.email}: ")
    abrir = build_opener(HTTPCookieProcessor(CookieJar())).open
    try:
        status, corpo = _requisitar(
            abrir, "POST", f"{args.api}/api/v1/auth/login", {"email": args.email, "senha": senha}
        )
        if status != 200:
            print(f"Login recusado ({status}): {corpo.get('erro', {}).get('mensagem', corpo)}")
            return 1
        print(
            f"Login ok. papel: {corpo['papel']} | "
            f"troca de senha obrigatória: {corpo['troca_senha_obrigatoria']}"
        )
        if corpo["papel"] == "admin":
            status, _ = _requisitar(abrir, "GET", f"{args.api}/api/v1/admin/resumo")
            print(f"Painel do administrador: {status}")
        _requisitar(abrir, "POST", f"{args.api}/api/v1/auth/logout")
    except OSError as erro:
        print(f"Não foi possível falar com a API em {args.api}: {erro}", file=sys.stderr)
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    comandos = parser.add_subparsers(dest="comando", required=True)

    gerar = comandos.add_parser("hash-senha", help="gera o hash da senha do administrador")
    gerar.set_defaults(executar=_hash_senha)

    vapid = comandos.add_parser("gerar-chaves-vapid", help="gera o par de chaves do push")
    vapid.set_defaults(executar=_gerar_chaves_vapid)

    lembretes = comandos.add_parser("enviar-lembretes", help="envia o resumo do dia por push")
    lembretes.set_defaults(executar=_enviar_lembretes)

    testar = comandos.add_parser("testar-login", help="entra na API com e-mail e senha")
    testar.add_argument("email")
    testar.add_argument("--api", default="http://localhost:8000")
    testar.set_defaults(executar=_testar_login)

    args = parser.parse_args(argv)
    return args.executar(args)


if __name__ == "__main__":
    raise SystemExit(main())
