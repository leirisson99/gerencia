import { requisitar } from "./client"
import type { LembreteLivre, LembreteLivreIn, LembreteLivrePatch } from "./types"

export function criarLembreteLivre(dados: LembreteLivreIn) {
  return requisitar<LembreteLivre>("/lembretes/livres", { metodo: "POST", corpo: dados })
}

export function editarLembreteLivre(id: number, dados: LembreteLivrePatch) {
  return requisitar<LembreteLivre>(`/lembretes/livres/${id}`, { metodo: "PATCH", corpo: dados })
}

export function excluirLembreteLivre(id: number) {
  return requisitar<void>(`/lembretes/livres/${id}`, { metodo: "DELETE" })
}
