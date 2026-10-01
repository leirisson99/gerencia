"""Comandos de servidor.

Uso:
  uv run python -m app.cli hash-senha   # gera o ADMIN_SENHA_HASH do .env
"""

import argparse
import sys
from getpass import getpass

from app.domain.usuario import validar_senha
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    comandos = parser.add_subparsers(dest="comando", required=True)

    gerar = comandos.add_parser("hash-senha", help="gera o hash da senha do administrador")
    gerar.set_defaults(executar=_hash_senha)

    args = parser.parse_args(argv)
    return args.executar(args)


if __name__ == "__main__":
    raise SystemExit(main())
