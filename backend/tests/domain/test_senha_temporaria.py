import string

from app.domain.usuario import validar_senha
from app.services.senha import gerar_senha_temporaria


def test_tem_12_letras_e_digitos_e_passa_na_regra_de_senha() -> None:
    for _ in range(200):
        senha = gerar_senha_temporaria()
        assert len(senha) == 12
        assert set(senha) <= set(string.ascii_letters + string.digits)
        assert validar_senha(senha) == senha


def test_cada_chamada_gera_uma_senha_diferente() -> None:
    assert len({gerar_senha_temporaria() for _ in range(50)}) == 50
