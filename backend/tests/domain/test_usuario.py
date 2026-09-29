from datetime import date

import pytest

from app.domain.usuario import (
    limpar_texto,
    normalizar_email,
    normalizar_telefone,
    validar_data_nascimento,
    validar_senha,
)

HOJE = date(2026, 9, 28)


class TestNormalizarEmail:
    def test_remove_espacos_e_minusculas(self) -> None:
        assert normalizar_email("  ANA@Exemplo.com ") == "ana@exemplo.com"

    @pytest.mark.parametrize("valor", ["", "ana", "ana@", "@exemplo.com", "ana exemplo@x.com"])
    def test_formato_invalido(self, valor: str) -> None:
        with pytest.raises(ValueError, match="E-mail inválido"):
            normalizar_email(valor)

    def test_mais_de_254_caracteres(self) -> None:
        with pytest.raises(ValueError):
            normalizar_email("a" * 64 + "@" + "b" * 190 + ".com")


class TestNormalizarTelefone:
    @pytest.mark.parametrize(
        ("valor", "esperado"),
        [
            ("(11) 98765-4321", "11987654321"),
            ("11987654321", "11987654321"),
            ("1133334444", "1133334444"),
            ("(21) 3333-4444", "2133334444"),
        ],
    )
    def test_aceita_com_ou_sem_mascara(self, valor: str, esperado: str) -> None:
        assert normalizar_telefone(valor) == esperado

    @pytest.mark.parametrize(
        "valor",
        [
            "123",  # curto
            "119876543210",  # 12 dígitos
            "0198765432",  # DDD 01
            "1087654321",  # DDD 10
            "11887654321",  # 11 dígitos sem o 9
            "abc",
        ],
    )
    def test_recusa_invalido(self, valor: str) -> None:
        with pytest.raises(ValueError):
            normalizar_telefone(valor)


class TestValidarSenha:
    @pytest.mark.parametrize("senha", ["abc12345", "Senha segura 1", "a1" * 64])
    def test_aceita(self, senha: str) -> None:
        assert validar_senha(senha) == senha

    @pytest.mark.parametrize(
        "senha",
        [
            "abcdefgh",  # sem número
            "12345678",  # sem letra
            "abc1234",  # 7 caracteres
            "a1" * 64 + "x",  # 129 caracteres
        ],
    )
    def test_recusa(self, senha: str) -> None:
        with pytest.raises(ValueError):
            validar_senha(senha)


class TestValidarDataNascimento:
    @pytest.mark.parametrize("data", [date(1900, 1, 1), date(1995, 3, 15), HOJE])
    def test_aceita_entre_1900_e_hoje(self, data: date) -> None:
        assert validar_data_nascimento(data, HOJE) == data

    @pytest.mark.parametrize("data", [date(1899, 12, 31), date(2026, 9, 29)])
    def test_recusa_fora_do_intervalo(self, data: date) -> None:
        with pytest.raises(ValueError):
            validar_data_nascimento(data, HOJE)


class TestLimparTexto:
    def test_remove_espacos_nas_pontas(self) -> None:
        assert limpar_texto("  Ana Souza ", 120) == "Ana Souza"

    @pytest.mark.parametrize("valor", ["", "   "])
    def test_vazio_e_obrigatorio(self, valor: str) -> None:
        with pytest.raises(ValueError, match="obrigatório"):
            limpar_texto(valor, 120)

    def test_acima_do_limite(self) -> None:
        with pytest.raises(ValueError, match="80"):
            limpar_texto("x" * 81, 80)
