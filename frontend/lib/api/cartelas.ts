import { requisitar } from "./client"
import type { Cartela, CartelaIn } from "./types"

export function criarCartela(dados: CartelaIn) {
  return requisitar<Cartela>("/cartelas", { metodo: "POST", corpo: dados })
}

/** Marca a casa com a data de hoje e lança a saída em "Poupança". */
export function depositar(cartelaId: number, casaId: number) {
  return requisitar<Cartela>(`/cartelas/${cartelaId}/casas/${casaId}/deposito`, { metodo: "POST" })
}

/** Libera a casa e remove o lançamento do depósito. */
export function desfazerDeposito(cartelaId: number, casaId: number) {
  return requisitar<Cartela>(`/cartelas/${cartelaId}/casas/${casaId}/deposito`, { metodo: "DELETE" })
}
