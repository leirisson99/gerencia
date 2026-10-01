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

const BARRA = { borderRadius: 4, borderSkipped: "start" as const, maxBarThickness: 28 }

/** Eixos de contagem: grade só no eixo do valor, ticks inteiros, sem bordas. */
function eixos() {
  return {
    x: { grid: { display: false }, border: { display: false }, ticks: { maxRotation: 0, autoSkipPadding: 12 } },
    y: {
      beginAtZero: true,
      grid: { color: token("--border") },
      border: { display: false },
      ticks: { maxTicksLimit: 5, precision: 0 },
    },
  }
}

function Vazio({ texto }: { texto: string }) {
  return <p className="py-10 text-center text-sm text-muted-foreground">{texto}</p>
}

/** Quantidade de entradas e saídas realizadas por mês, somando todas as contas. */
export function GraficoMovimentacoes({ meses }: { meses: ResumoAdmin["por_mes"] }) {
  const canvas = useRef<HTMLCanvasElement>(null)
  const total = meses.reduce((soma, m) => soma + m.entradas + m.saidas, 0)

  useGrafico(
    canvas,
    () => ({
      type: "bar",
      data: {
        labels: meses.map((m) => rotuloMes(m.mes)),
        datasets: [
          { label: "Entradas", data: meses.map((m) => m.entradas), backgroundColor: token("--foreground"), ...BARRA },
          { label: "Saídas", data: meses.map((m) => m.saidas), backgroundColor: token("--destructive"), ...BARRA },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        datasets: { bar: { categoryPercentage: 0.6, barPercentage: 0.9 } },
        interaction: { mode: "index", intersect: false },
        scales: eixos(),
        plugins: {
          legend: { display: false },
          tooltip: { callbacks: { label: (item) => ` ${item.dataset.label}: ${item.raw as number}` } },
        },
      },
    }),
    [meses]
  )

  if (total === 0) return <Vazio texto="Nenhuma movimentação realizada nos últimos 12 meses." />

  // Resumo em texto para leitor de tela e para quem não vê o canvas.
  const rotulo = `Entradas e saídas realizadas nos últimos ${meses.length} meses: ${meses
    .map((m) => `${rotuloMes(m.mes)}, ${m.entradas} entradas e ${m.saidas} saídas`)
    .join("; ")}`

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

/** Contas criadas em cada mês, do mais antigo ao atual. */
export function GraficoCadastros({ meses }: { meses: ResumoAdmin["cadastros_por_mes"] }) {
  const canvas = useRef<HTMLCanvasElement>(null)
  const total = meses.reduce((soma, m) => soma + m.quantidade, 0)

  useGrafico(
    canvas,
    () => ({
      type: "bar",
      data: {
        labels: meses.map((m) => rotuloMes(m.mes)),
        datasets: [
          { label: "Cadastros", data: meses.map((m) => m.quantidade), backgroundColor: token("--foreground"), ...BARRA },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        datasets: { bar: { categoryPercentage: 0.6, barPercentage: 0.9 } },
        scales: eixos(),
        plugins: {
          legend: { display: false },
          tooltip: { displayColors: false, callbacks: { label: (item) => `Cadastros: ${item.raw as number}` } },
        },
      },
    }),
    [meses]
  )

  if (total === 0) return <Vazio texto="Nenhum cadastro nos últimos 12 meses." />

  const rotulo = `Cadastros nos últimos ${meses.length} meses: ${meses
    .map((m) => `${rotuloMes(m.mes)}, ${m.quantidade}`)
    .join("; ")}`

  // Sem legenda: a margem alinha o gráfico com o de movimentações ao lado.
  return (
    <div className="relative h-56 lg:mt-8">
      <canvas ref={canvas} role="img" aria-label={rotulo} />
    </div>
  )
}
