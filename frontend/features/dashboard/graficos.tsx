"use client"

import { useRef } from "react"
import {
  BarController,
  BarElement,
  CategoryScale,
  Chart,
  Filler,
  LinearScale,
  LineController,
  LineElement,
  PointElement,
  Tooltip,
} from "chart.js"

import { formatarCentavos, formatarCentavosCompacto } from "@/lib/format"
import { token, useGrafico } from "./use-grafico"

Chart.register(
  BarController,
  BarElement,
  CategoryScale,
  Filler,
  LinearScale,
  LineController,
  LineElement,
  PointElement,
  Tooltip
)

/** Eixos discretos: grade só no eixo do valor, sem bordas. */
function eixos() {
  return {
    x: { grid: { display: false }, border: { display: false }, ticks: { maxRotation: 0, autoSkipPadding: 12 } },
    y: {
      grid: { color: token("--border") },
      border: { display: false },
      ticks: { maxTicksLimit: 5, callback: (v: string | number) => formatarCentavosCompacto(Number(v)) },
    },
  }
}

export type PontoSaldo = { rotulo: string; saldo: number }

/** Saldo acumulado dia a dia no ciclo (ou mês): só o que foi realizado e conta no saldo. */
export function GraficoSaldo({ pontos, rotulo }: { pontos: PontoSaldo[]; rotulo: string }) {
  const canvas = useRef<HTMLCanvasElement>(null)

  useGrafico(
    canvas,
    () => {
      const cor = token("--foreground")
      const negativo = token("--destructive")
      return {
        type: "line",
        data: {
          labels: pontos.map((p) => p.rotulo),
          datasets: [
            {
              label: "Saldo",
              data: pontos.map((p) => p.saldo),
              borderColor: cor,
              borderWidth: 2,
              // Abaixo de zero a linha fica na cor de saída.
              segment: { borderColor: (ctx) => ((ctx.p1.parsed.y ?? 0) < 0 ? negativo : undefined) },
              // Token vem como `oklch(L C H)`; o preenchimento é a mesma cor quase transparente.
              backgroundColor: cor.replace(")", " / 0.06)"),
              fill: "origin",
              tension: 0.25,
              pointRadius: 0,
              pointHoverRadius: 4,
              pointHoverBackgroundColor: cor,
              pointHoverBorderColor: token("--card"),
              pointHoverBorderWidth: 2,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          interaction: { mode: "index", intersect: false },
          scales: eixos(),
          plugins: {
            legend: { display: false },
            tooltip: {
              displayColors: false,
              callbacks: { label: (item) => `Saldo: ${formatarCentavos(item.raw as number)}` },
            },
          },
        },
      }
    },
    [pontos]
  )

  return (
    <div className="relative h-56">
      <canvas ref={canvas} role="img" aria-label={rotulo} />
    </div>
  )
}

export type PeriodoTotais = { rotulo: string; entradas: number; saidas: number }

/** Entradas e saídas lado a lado por ciclo (ou mês), do mais antigo ao atual. */
export function GraficoEntradasSaidas({
  periodos,
  rotulo,
}: {
  periodos: PeriodoTotais[]
  rotulo: string
}) {
  const canvas = useRef<HTMLCanvasElement>(null)

  useGrafico(
    canvas,
    () => {
      const barra = { borderRadius: 4, borderSkipped: "start" as const, maxBarThickness: 28 }
      return {
        type: "bar",
        data: {
          labels: periodos.map((p) => p.rotulo),
          datasets: [
            { label: "Entradas", data: periodos.map((p) => p.entradas), backgroundColor: token("--foreground"), ...barra },
            { label: "Saídas", data: periodos.map((p) => p.saidas), backgroundColor: token("--destructive"), ...barra },
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
            tooltip: {
              callbacks: {
                label: (item) => ` ${item.dataset.label}: ${formatarCentavos(item.raw as number)}`,
                footer: (itens) => {
                  const [entradas, saidas] = [itens[0]?.raw, itens[1]?.raw] as number[]
                  return entradas !== undefined && saidas !== undefined
                    ? `Saldo: ${formatarCentavos(entradas - saidas)}`
                    : ""
                },
              },
            },
          },
        },
      }
    },
    [periodos]
  )

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
