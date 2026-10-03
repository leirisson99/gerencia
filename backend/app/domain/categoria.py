"""Categorias que todo usuário recebe no cadastro."""

from dataclasses import dataclass

NOME_SALARIO = "Salário"
NOME_POUPANCA = "Poupança"
NOME_RETIRADA_PJ = "Retirada para PF"
NOME_PRO_LABORE = "Pró-labore e lucros"


@dataclass(frozen=True)
class CategoriaInicial:
    nome: str
    tipo: str
    sistema: bool = False


CATEGORIAS_INICIAIS: tuple[CategoriaInicial, ...] = (
    CategoriaInicial(NOME_SALARIO, "entrada", sistema=True),
    CategoriaInicial("Renda extra", "entrada"),
    CategoriaInicial("Moradia", "saida"),
    CategoriaInicial("Alimentação", "saida"),
    CategoriaInicial("Transporte", "saida"),
    CategoriaInicial("Saúde", "saida"),
    CategoriaInicial("Lazer", "saida"),
    CategoriaInicial("Outros", "saida"),
    # Recebe os depósitos das cartelas.
    CategoriaInicial(NOME_POUPANCA, "saida", sistema=True),
)

# Criadas quando o usuário liga a carteira PJ: os dois lados de cada retirada.
CATEGORIAS_PJ: tuple[CategoriaInicial, ...] = (
    CategoriaInicial(NOME_RETIRADA_PJ, "saida", sistema=True),
    CategoriaInicial(NOME_PRO_LABORE, "entrada", sistema=True),
)


def e_categoria_salario(nome: str, sistema: bool) -> bool:
    """Só a categoria de sistema "Salário" abre ciclo."""
    return sistema and nome == NOME_SALARIO


def edicao_permitida(sistema: bool, muda_nome: bool, desativa: bool) -> bool:
    """Categorias do sistema (Salário, Poupança e as da PJ) não mudam de nome nem desativam."""
    return not (sistema and (muda_nome or desativa))
