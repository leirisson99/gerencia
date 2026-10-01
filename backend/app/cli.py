"""Comandos de servidor.

Uso:
  uv run python -m app.cli hash-senha          # gera o ADMIN_SENHA_HASH do .env
  uv run python -m app.cli gerar-chaves-vapid  # gera as chaves do push (VAPID_*) do .env
"""

import argparse
import sys
from getpass import getpass

from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from py_vapid import Vapid
from py_vapid.utils import b64urlencode

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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    comandos = parser.add_subparsers(dest="comando", required=True)

    gerar = comandos.add_parser("hash-senha", help="gera o hash da senha do administrador")
    gerar.set_defaults(executar=_hash_senha)

    vapid = comandos.add_parser("gerar-chaves-vapid", help="gera o par de chaves do push")
    vapid.set_defaults(executar=_gerar_chaves_vapid)

    args = parser.parse_args(argv)
    return args.executar(args)


if __name__ == "__main__":
    raise SystemExit(main())
