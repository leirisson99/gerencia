import type { Categoria, Lancamento } from "@/lib/api/types"
import { formatarData } from "@/lib/format"

/** Texto curto do lançamento para confirmações e leitores de tela: "Mercado de 05/10/2026". */
export function rotuloLancamento(lancamento: Lancamento, categorias: Categoria[]): string {
  const categoria = categorias.find((c) => c.id === lancamento.categoria_id)?.nome ?? "Lançamento"
  return `${lancamento.descricao || categoria} de ${formatarData(lancamento.data)}`
}
