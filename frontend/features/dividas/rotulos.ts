import type { Direcao, FormaPagamento } from "@/lib/api/types"

export const DIRECOES: Record<Direcao, string> = {
  devo: "Eu devo",
  me_devem: "Me devem",
}

export const FORMAS: Record<FormaPagamento, string> = {
  pix: "Pix",
  boleto: "Boleto",
  cartao: "Cartão de crédito",
  dinheiro: "Dinheiro",
}

/** Texto do botão que confirma uma parcela prevista. */
export function rotuloConfirmarParcela(direcao: Direcao) {
  return direcao === "devo" ? "Marcar paga" : "Marcar recebida"
}
