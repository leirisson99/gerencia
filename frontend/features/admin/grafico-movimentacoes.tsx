"use client"

import { useRef } from "react"
import { BarController, BarElement, CategoryScale, Chart, LinearScale, Tooltip } from "chart.js"

import { token, useGrafico } from "@/features/dashboard/use-grafico"
import type { ResumoAdmin } from "@/lib/api/types"

Chart.register(BarController, BarElement, CategoryScale, LinearScale, Tooltip)

const mesCurto = new Intl.DateTimeFormat("pt-BR", { month: "short", year: "2-digit", timeZone: "UTC" })

/** `2026-09` → `set. 26` */
function rotuloMes(mes: string) {
  return mesCurto.format(new Date(`${mes}-01T00:00:00Z`))
}

/** Quantidade de entradas e saídas realizadas por mês, somando todas as contas. */
export function GraficoMovimentacoes({ meses }: { meses: ResumoAdmin["por_mes"] }) {
  const canvas = useRef<HTMLCanvasElement>(null)
  const total = meses.reduce((soma, m) => soma + m.entradas + m.saidas, 0)

  useGrafico(
    canvas,
    () => {
      const barra = { borderRadius: 4, borderSkipped: "start" as const, maxBarThickness: 28 }
      return {
        type: "bar",
        data: {
          labels: meses.map((m) => rotuloMes(m.mes)),
          datasets: [
            { label: "Entradas", data: meses.map((m) => m.entradas), backgroundColor: token("--foreground"), ...barra },
            { label: "Saídas", data: meses.map((m) => m.saidas), backgroundColor: token("--destructive"), ...barra },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          datasets: { bar: { categoryPercentage: 0.6, barPercentage: 0.9 } },
          interaction: { mode: "index", intersect: false },
          scales: {
            x: { grid: { display: false }, border: { display: false }, ticks: { maxRotation: 0, autoSkipPadding: 12 } },
            y: {
              beginAtZero: true,
              grid: { color: token("--border") },
              border: { display: false },
              ticks: { maxTicksLimit: 5, precision: 0 },
            },
          },
          plugins: {
            legend: { display: false },
            tooltip: {
              callbacks: { label: (item) => ` ${item.dataset.label}: ${item.raw as number}` },
            },
          },
        },
      }
    },
    [meses]
  )

  // Resumo em texto para leitor de tela e para quem não vê o canvas.
  const rotulo = `Entradas e saídas realizadas nos últimos ${meses.length} meses: ${meses
    .map((m) => `${rotuloMes(m.mes)}, ${m.entradas} entradas e ${m.saidas} saídas`)
    .join("; ")}`

  if (total === 0) {
    return <p className="py-10 text-center text-sm text-muted-foreground">Nenhuma movimentação realizada nos últimos 12 meses.</p>
  }

  return (
    <>
      <ul className="mb-3 flex gap-4 text-sm text-muted-foreground" aria-hidden>
        <li className="flex items-center gap-2">
          <span className="size-2.5 rounded-sm bg-foreground" /> Entradas
        </li>
        <li className="flex items-center gap-2">
          <span className="size-2.5 rounded-sm bg-saida" /> Saídas
        </li>
      </ul>
      <div className="relative h-56">
        <canvas ref={canvas} role="img" aria-label={rotulo} />
      </div>
    </>
  )
}
