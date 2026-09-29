import secrets
import string

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

_hasher = PasswordHasher()

TAMANHO_SENHA_TEMPORARIA = 12
_ALFABETO = string.ascii_letters + string.digits


def gerar_senha_temporaria() -> str:
    """12 letras e dígitos aleatórios, com pelo menos uma letra e um dígito."""
    while True:
        senha = "".join(secrets.choice(_ALFABETO) for _ in range(TAMANHO_SENHA_TEMPORARIA))
        if any(c.isalpha() for c in senha) and any(c.isdigit() for c in senha):
            return senha


def hash_senha(senha: str) -> str:
    return _hasher.hash(senha)


def verificar_senha(senha_hash: str, senha: str) -> bool:
    try:
        return _hasher.verify(senha_hash, senha)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def precisa_rehash(senha_hash: str) -> bool:
    return _hasher.check_needs_rehash(senha_hash)


# Usado quando o e-mail não existe, para o login levar o mesmo tempo nos dois casos.
HASH_FICTICIO = hash_senha("senha-ficticia-para-igualar-tempo")
