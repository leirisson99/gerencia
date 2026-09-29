import { requisitar } from "./client"
import type { Divida, DividaIn } from "./types"

/** Cria a dívida e todas as parcelas como lançamentos previstos. */
export function criarDivida(dados: DividaIn) {
  return requisitar<Divida>("/dividas", { metodo: "POST", corpo: dados })
}
