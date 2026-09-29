import { requisitar } from "./client"
import type { Lancamento, LancamentoIn, LancamentoPatch } from "./types"

export function criarLancamento(dados: LancamentoIn) {
  return requisitar<Lancamento>("/lancamentos", { metodo: "POST", corpo: dados })
}

export function editarLancamento(id: number, dados: LancamentoPatch) {
  return requisitar<Lancamento>(`/lancamentos/${id}`, { metodo: "PATCH", corpo: dados })
}

export function excluirLancamento(id: number) {
  return requisitar<void>(`/lancamentos/${id}`, { metodo: "DELETE" })
}
