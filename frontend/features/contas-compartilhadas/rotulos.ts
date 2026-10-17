import type { ModoDivisao, StatusCota, StatusParticipante } from "@/lib/api/types"

export const MODOS: Record<ModoDivisao, string> = {
  igual: "Igual para todos",
  percentual: "Percentual por pessoa",
  fixo: "Valor fixo por pessoa",
}

export const DESCRICAO_MODOS: Record<ModoDivisao, string> = {
  igual: "O total é dividido igualmente entre quem aceitou. O resto de centavos vai para o último.",
  percentual: "Cada pessoa paga uma porcentagem do total. A soma de quem aceitou tem de dar 100%.",
  fixo: "Cada pessoa paga um valor combinado. A soma de quem aceitou tem de dar o total.",
}

export const STATUS_PARTICIPANTE: Record<StatusParticipante, string> = {
  pendente: "Convite pendente",
  aceito: "Aceitou",
  recusado: "Recusou",
  removido: "Removido",
  saiu: "Saiu",
}

export const STATUS_COTA: Record<StatusCota, string> = {
  pendente: "Pendente",
  informado: "Informou o pagamento",
  confirmado: "Confirmado",
}

/** `3334` pontos-base → `33,34`. Só inteiros: sem passar por float. */
export function textoDeBps(bps: number): string {
  const inteiro = Math.floor(bps / 100)
  const resto = String(bps % 100).padStart(2, "0")
  return resto === "00" ? String(inteiro) : `${inteiro},${resto}`
}

/** `33,34` → `3334` pontos-base; `null` se não for um percentual válido de 0 a 100. */
export function bpsDeTexto(texto: string): number | null {
  const limpo = texto.trim().replace("%", "").replace(".", ",")
  const partes = limpo.split(",")
  if (partes.length > 2 || !/^\d{1,3}$/.test(partes[0])) return null
  const decimais = partes[1] ?? ""
  if (decimais !== "" && !/^\d{1,2}$/.test(decimais)) return null
  const bps = Number(partes[0]) * 100 + Number(decimais.padEnd(2, "0"))
  return bps <= 10_000 ? bps : null
}

/** "1 pessoa", "3 pessoas". */
export function rotuloPessoas(qtd: number): string {
  return `${qtd} ${qtd === 1 ? "pessoa" : "pessoas"}`
}

/** "2 convites pendentes" ou `null` quando não há nenhum. */
export function rotuloPendentes(qtd: number): string | null {
  if (qtd === 0) return null
  return `${qtd} ${qtd === 1 ? "convite pendente" : "convites pendentes"}`
}
