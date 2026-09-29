import { requisitar } from "./client"
import type { Categoria, CategoriaIn, CategoriaPatch } from "./types"

export function criarCategoria(dados: CategoriaIn) {
  return requisitar<Categoria>("/categorias", { metodo: "POST", corpo: dados })
}

export function editarCategoria(id: number, dados: CategoriaPatch) {
  return requisitar<Categoria>(`/categorias/${id}`, { metodo: "PATCH", corpo: dados })
}
