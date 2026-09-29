import { requisitar } from "./client"
import type { LancamentoComAviso, LancamentoIn, LancamentoPatch } from "./types"

export function criarLancamento(dados: LancamentoIn) {
  return requisitar<LancamentoComAviso>("/lancamentos", { metodo: "POST", corpo: dados })
}

export function editarLancamento(id: number, dados: LancamentoPatch) {
  return requisitar<LancamentoComAviso>(`/lancamentos/${id}`, { metodo: "PATCH", corpo: dados })
}

export function excluirLancamento(id: number) {
  return requisitar<void>(`/lancamentos/${id}`, { metodo: "DELETE" })
}
