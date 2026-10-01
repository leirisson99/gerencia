import { requisitar } from "./client"
import type { RecebimentoIn, Servico, ServicoIn, ServicoPatch } from "./types"

/** Cria o serviço e a entrada prevista na data prevista. */
export function criarServico(dados: ServicoIn) {
  return requisitar<Servico>("/servicos", { metodo: "POST", corpo: dados })
}

/** Só enquanto não recebido; a entrada prevista acompanha. */
export function editarServico(id: number, dados: ServicoPatch) {
  return requisitar<Servico>(`/servicos/${id}`, { metodo: "PATCH", corpo: dados })
}

/** Remove o serviço e a entrada prevista. Recebido, desfaça o recebimento antes. */
export function excluirServico(id: number) {
  return requisitar<void>(`/servicos/${id}`, { metodo: "DELETE" })
}

/** A entrada vira realizada com a data e o valor recebidos. */
export function receberServico(id: number, dados: RecebimentoIn) {
  return requisitar<Servico>(`/servicos/${id}/recebimento`, { metodo: "POST", corpo: dados })
}

/** A entrada volta a prevista, com a data prevista e o valor combinado. */
export function desfazerRecebimento(id: number) {
  return requisitar<Servico>(`/servicos/${id}/recebimento`, { metodo: "DELETE" })
}
