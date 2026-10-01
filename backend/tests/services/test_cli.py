from typing import Any

import pytest

from app import cli
from app.services.senha import verificar_senha


def digitar(monkeypatch: pytest.MonkeyPatch, *respostas: str) -> None:
    fila = list(respostas)
    monkeypatch.setattr(cli, "getpass", lambda _prompt="": fila.pop(0))


def test_hash_senha_imprime_um_hash_que_confere(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    digitar(monkeypatch, "segredoAdmin1", "segredoAdmin1")

    assert cli.main(["hash-senha"]) == 0

    saida = capsys.readouterr().out
    linha = next(linha for linha in saida.splitlines() if linha.startswith("ADMIN_SENHA_HASH="))
    hash_ = linha.removeprefix("ADMIN_SENHA_HASH=").strip("'")
    assert verificar_senha(hash_, "segredoAdmin1")
    assert "segredoAdmin1" not in saida


def test_hash_senha_recusa_confirmacao_diferente(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    digitar(monkeypatch, "segredoAdmin1", "segredoAdmin2")

    assert cli.main(["hash-senha"]) == 1
    assert "não conferem" in capsys.readouterr().err


def test_hash_senha_segue_a_regra_de_senha(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    digitar(monkeypatch, "curta", "curta")

    assert cli.main(["hash-senha"]) == 1
    assert "caracteres" in capsys.readouterr().err


def _variavel(saida: str, nome: str) -> str:
    return next(linha for linha in saida.splitlines() if linha.startswith(f"{nome}=")).split(
        "=", 1
    )[1]


def test_gerar_chaves_vapid_imprime_par_valido(capsys: pytest.CaptureFixture[str]) -> None:
    from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
    from py_vapid import Vapid
    from py_vapid.utils import b64urldecode, b64urlencode

    assert cli.main(["gerar-chaves-vapid"]) == 0

    saida = capsys.readouterr().out
    publica = _variavel(saida, "VAPID_CHAVE_PUBLICA")
    privada = _variavel(saida, "VAPID_CHAVE_PRIVADA")
    # applicationServerKey do navegador: ponto não comprimido P-256 (65 bytes, começa em 0x04).
    assert len(b64urldecode(publica.encode())) == 65
    assert b64urldecode(publica.encode())[0] == 4
    # O pywebpush aceita a privada em base64url e ela corresponde à pública impressa.
    derivada = Vapid.from_raw(privada.encode()).public_key.public_bytes(
        Encoding.X962, PublicFormat.UncompressedPoint
    )
    assert b64urlencode(derivada) == publica


def test_gerar_chaves_vapid_gera_par_novo_a_cada_vez(capsys: pytest.CaptureFixture[str]) -> None:
    cli.main(["gerar-chaves-vapid"])
    primeira = capsys.readouterr().out
    cli.main(["gerar-chaves-vapid"])
    assert capsys.readouterr().out != primeira


def _settings(**vapid: str | None) -> Any:
    from app.config import Settings

    # Valores explícitos: o .env de desenvolvimento pode ter chaves de verdade.
    vazio: dict[str, str | None] = dict.fromkeys(
        ("vapid_chave_publica", "vapid_chave_privada", "vapid_contato")
    )
    return Settings(database_url="postgresql+psycopg://x@localhost/x", **{**vazio, **vapid})


def test_enviar_lembretes_sem_chaves_vapid_falha(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(cli, "get_settings", lambda: _settings())

    assert cli.main(["enviar-lembretes"]) == 1
    assert "VAPID" in capsys.readouterr().err


def test_enviar_lembretes_imprime_so_contagens(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from contextlib import nullcontext
    from datetime import date

    from py_vapid import Vapid
    from py_vapid.utils import b64urlencode

    from app.services.envio_lembrete import Relatorio

    vapid = Vapid()
    vapid.generate_keys()
    privada = b64urlencode(vapid.private_key.private_numbers().private_value.to_bytes(32, "big"))
    monkeypatch.setattr(
        cli,
        "get_settings",
        lambda: _settings(
            vapid_chave_publica="publica",
            vapid_chave_privada=privada,
            vapid_contato="mailto:admin@exemplo.com",
        ),
    )
    monkeypatch.setattr(cli, "SessionLocal", lambda: nullcontext("db"))
    chamadas: list[tuple[Any, date]] = []

    def enviar(db: Any, hoje: date, enviador: Any) -> Relatorio:
        chamadas.append((db, hoje))
        return Relatorio(usuarios=3, enviados=1, sem_pendencias=1, ja_enviados=1, removidos=2)

    monkeypatch.setattr(cli, "enviar_lembretes_do_dia", enviar)

    assert cli.main(["enviar-lembretes"]) == 0

    assert chamadas == [("db", cli.Relogio().hoje_sp())]
    assert capsys.readouterr().out.strip() == (
        "usuarios=3 enviados=1 sem_pendencias=1 ja_enviados=1 removidos=2 falhas=0"
    )
