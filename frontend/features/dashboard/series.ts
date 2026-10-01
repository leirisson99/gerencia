import type { PeriodoTotais, PontoSaldo } from "@/features/dashboard/graficos"
import type { Lancamento, ResumoCiclo } from "@/lib/api/types"
import { formatarDiaMes } from "@/lib/format"

const mesCurto = new Intl.DateTimeFormat("pt-BR", { month: "short", timeZone: "UTC" })

/** Dia seguinte de uma data ISO. */
function proximoDia(iso: string): string {
  const d = new Date(`${iso}T00:00:00Z`)
  d.setUTCDate(d.getUTCDate() + 1)
  return d.toISOString().slice(0, 10)
}

/**
 * Saldo acumulado ao fim de cada dia, de `inicio` até `ate`. Segue a regra do resumo da API:
 * só conta o que está realizado e entra no saldo (parcela no cartão, por exemplo, não).
 */
export function saldoDiaADia(lancamentos: Lancamento[], inicio: string, ate: string): PontoSaldo[] {
  const porDia = new Map<string, number>()
  for (const l of lancamentos) {
    if (l.status !== "realizado" || !l.conta_no_saldo) continue
    const sinal = l.tipo === "entrada" ? 1 : -1
    porDia.set(l.data, (porDia.get(l.data) ?? 0) + sinal * l.valor)
  }

  const pontos: PontoSaldo[] = []
  let saldo = 0
  for (let dia = inicio; dia <= ate; dia = proximoDia(dia)) {
    saldo += porDia.get(dia) ?? 0
    pontos.push({ rotulo: formatarDiaMes(dia), saldo })
  }
  return pontos
}

/** Rótulo curto de um ciclo no eixo: o mês (`set.`) para o prestador, a data de início para o CLT. */
export function rotuloPeriodo(inicio: string, mensal: boolean): string {
  return mensal ? mesCurto.format(new Date(`${inicio}T00:00:00Z`)) : formatarDiaMes(inicio)
}

/** Totais dos resumos, do mais antigo ao mais recente, para o gráfico de barras. */
export function totaisPorPeriodo(resumos: ResumoCiclo[], mensal: boolean): PeriodoTotais[] {
  return resumos
    .map((r) => ({ rotulo: rotuloPeriodo(r.ciclo.inicio, mensal), entradas: r.entradas, saidas: r.saidas }))
    .reverse()
}
