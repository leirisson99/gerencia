// Datas do calendário como texto ISO, calculadas em UTC para não depender do fuso do navegador.

const ISO_MES = /^\d{4}-(0[1-9]|1[0-2])$/

export function mesValido(mes: string): boolean {
  return ISO_MES.test(mes)
}

function partes(mes: string): [number, number] {
  const [ano, m] = mes.split("-").map(Number)
  return [ano, m]
}

function iso(data: Date): string {
  return data.toISOString().slice(0, 10)
}

/** Primeiro e último dia do mês `YYYY-MM`. */
export function limitesDoMes(mes: string): { inicio: string; fim: string } {
  const [ano, m] = partes(mes)
  return { inicio: `${mes}-01`, fim: iso(new Date(Date.UTC(ano, m, 0))) }
}

/** Mês anterior (`-1`) ou seguinte (`1`). */
export function mesVizinho(mes: string, passo: -1 | 1): string {
  const [ano, m] = partes(mes)
  return iso(new Date(Date.UTC(ano, m - 1 + passo, 1))).slice(0, 7)
}

/** Semanas do mês começando no domingo; `null` nas casas fora do mês. */
export function semanasDoMes(mes: string): (string | null)[][] {
  const [ano, m] = partes(mes)
  const primeiro = new Date(Date.UTC(ano, m - 1, 1))
  const dias = new Date(Date.UTC(ano, m, 0)).getUTCDate()
  const casas: (string | null)[] = Array(primeiro.getUTCDay()).fill(null)
  for (let dia = 1; dia <= dias; dia++) casas.push(`${mes}-${String(dia).padStart(2, "0")}`)
  while (casas.length % 7) casas.push(null)
  return Array.from({ length: casas.length / 7 }, (_, i) => casas.slice(i * 7, i * 7 + 7))
}
