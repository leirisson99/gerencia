import type { Categoria } from "@/lib/api/types"

// Espelha e_categoria_salario de backend/app/domain/categoria.py: há mais de uma categoria de
// sistema (Salário, Poupança), e só "Salário" abre ciclo.
const NOME_SALARIO = "Salário"

export function eSalario(categoria: Pick<Categoria, "nome" | "sistema">): boolean {
  return categoria.sistema && categoria.nome === NOME_SALARIO
}

export function acharSalario(categorias: Categoria[]): Categoria | undefined {
  return categorias.find(eSalario)
}

// Espelha CATEGORIAS_PJ de backend/app/domain/categoria.py: os dois lados de cada retirada.
const NOMES_RETIRADA = ["Retirada para PF", "Pró-labore e lucros"]

/** Categoria de sistema usada só pela retirada da PJ; não aparece nos lançamentos à mão. */
export function eDeRetirada(categoria: Pick<Categoria, "nome" | "sistema">): boolean {
  return categoria.sistema && NOMES_RETIRADA.includes(categoria.nome)
}
