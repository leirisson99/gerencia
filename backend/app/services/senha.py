from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

_hasher = PasswordHasher()


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
