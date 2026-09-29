"""Categorias que todo usuário recebe no cadastro."""

from dataclasses import dataclass

NOME_SALARIO = "Salário"


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
)


def e_categoria_salario(nome: str, sistema: bool) -> bool:
    """Só a categoria de sistema "Salário" abre ciclo."""
    return sistema and nome == NOME_SALARIO


def edicao_permitida(e_salario: bool, muda_nome: bool, desativa: bool) -> bool:
    """A categoria que abre ciclo não pode mudar de nome nem ser desativada."""
    return not (e_salario and (muda_nome or desativa))
