import type { Servico, SituacaoServico } from "@/lib/api/types"
import { formatarData } from "@/lib/format"

export const ROTULO_SITUACAO: Record<SituacaoServico, string> = {
  a_receber: "A receber",
  atrasado: "Atrasado",
  recebido: "Recebido",
}

/** `Cliente — descrição` ou só o cliente, como na entrada que o serviço gera. */
export function rotuloServico(servico: Pick<Servico, "cliente" | "descricao">): string {
  return servico.descricao ? `${servico.cliente} — ${servico.descricao}` : servico.cliente
}

/** `Recebido em 05/10/2026`, `Atrasado desde 05/10/2026` ou `Previsto para 05/10/2026`. */
export function detalheSituacao(servico: Servico): string {
  if (servico.situacao === "recebido" && servico.data_recebimento) {
    return `Recebido em ${formatarData(servico.data_recebimento)}`
  }
  if (servico.situacao === "atrasado") return `Atrasado desde ${formatarData(servico.data_prevista)}`
  return `Previsto para ${formatarData(servico.data_prevista)}`
}
