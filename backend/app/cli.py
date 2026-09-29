"""Comandos de servidor. Uso: uv run python -m app.cli criar-admin --nome ... --email ..."""

import argparse
import sys

from pydantic import ValidationError

from app.db import SessionLocal
from app.erros import ErroApi
from app.relogio import Relogio
from app.schemas.admin import DadosAdmin
from app.services.admin import criar_administrador


def _criar_admin(args: argparse.Namespace) -> int:
    try:
        dados = DadosAdmin(
            nome=args.nome, email=args.email, telefone=args.telefone, cargo=args.cargo
        )
    except ValidationError as erro:
        for item in erro.errors():
            campo = ".".join(str(parte) for parte in item["loc"])
            mensagem = (item.get("ctx") or {}).get("error", item["msg"])
            print(f"{campo}: {mensagem}", file=sys.stderr)
        return 1

    with SessionLocal() as db:
        try:
            _, senha = criar_administrador(db, dados, Relogio().agora_utc())
        except ErroApi as erro:
            print(erro.mensagem, file=sys.stderr)
            return 1

    print(f"Administrador criado. Senha temporária (troque no primeiro login): {senha}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    comandos = parser.add_subparsers(dest="comando", required=True)

    criar = comandos.add_parser("criar-admin", help="cria o único administrador")
    for campo in ("nome", "email", "telefone", "cargo"):
        criar.add_argument(f"--{campo}", required=True)
    criar.set_defaults(executar=_criar_admin)

    args = parser.parse_args(argv)
    return args.executar(args)


if __name__ == "__main__":
    raise SystemExit(main())
