import { requisitar } from "./client"
import type { Retirada, RetiradaIn } from "./types"

/** Registra a saída na PJ e a entrada na PF de uma vez. */
export function criarRetirada(dados: RetiradaIn) {
  return requisitar<Retirada>("/retiradas", { metodo: "POST", corpo: dados })
}

/** Muda os dois lados juntos. */
export function editarRetirada(id: number, dados: Partial<RetiradaIn>) {
  return requisitar<Retirada>(`/retiradas/${id}`, { metodo: "PATCH", corpo: dados })
}

/** Remove a retirada e os dois lançamentos dela. */
export function excluirRetirada(id: number) {
  return requisitar<void>(`/retiradas/${id}`, { metodo: "DELETE" })
}
