"use client"

import { useRef } from "react"
import { ArcElement, Chart, PieController, Tooltip } from "chart.js"

import type { TotalCategoria } from "@/lib/api/types"
import { formatarCentavos } from "@/lib/format"
import { token, useGrafico } from "./use-grafico"

Chart.register(PieController, ArcElement, Tooltip)

/** Fatias com cor própria; o que passar disso vira "Outros" na última. */
const FATIAS = 5

type Fatia = { nome: string; total: number }

/** Maiores categorias primeiro (a API já ordena); as menores se juntam em "Outros". */
function agrupar(totais: TotalCategoria[]): Fatia[] {
  if (totais.length <= FATIAS) return totais.map(({ nome, total }) => ({ nome, total }))
  const resto = totais.slice(FATIAS - 1).reduce((s, t) => s + t.total, 0)
  return [
    ...totais.slice(0, FATIAS - 1).map(({ nome, total }) => ({ nome, total })),
    { nome: "Outros", total: resto },
  ]
}

const percentual = (valor: number, soma: number) => (soma > 0 ? Math.round((valor * 100) / soma) : 0)

/**
 * Pizza de uma soma por categoria. A legenda ao lado traz nome, valor e percentual escritos,
 * então a cor nunca é a única pista de qual fatia é qual.
 */
export function GraficoPizza({
  totais,
  soma,
  vazio,
  rotulo,
}: {
  totais: TotalCategoria[]
  soma: number
  vazio: string
  /** Descrição do gráfico para leitor de tela. */
  rotulo: string
}) {
  const canvas = useRef<HTMLCanvasElement>(null)
  const fatias = agrupar(totais)

  useGrafico(
    canvas,
    () =>
      fatias.length === 0
        ? null
        : {
            type: "pie",
            data: {
              labels: fatias.map((f) => f.nome),
              datasets: [
                {
                  data: fatias.map((f) => f.total),
                  backgroundColor: fatias.map((_, i) => token(`--chart-${i + 1}`)),
                  borderColor: token("--card"),
                  borderWidth: 2,
                  hoverOffset: 6,
                },
              ],
            },
            options: {
              responsive: true,
              maintainAspectRatio: false,
              layout: { padding: 6 },
              plugins: {
                legend: { display: false },
                tooltip: {
                  callbacks: {
                    label: (item) => {
                      const valor = item.raw as number
                      return ` ${formatarCentavos(valor)} · ${percentual(valor, soma)}%`
                    },
                  },
                },
              },
            },
          },
    [totais, soma]
  )

  if (fatias.length === 0) return <p className="py-6 text-muted-foreground">{vazio}</p>

  return (
    <div className="flex flex-col items-center gap-5 sm:flex-row lg:flex-col xl:flex-row">
      <div className="relative size-40 shrink-0">
        <canvas ref={canvas} role="img" aria-label={rotulo} />
      </div>
      <ul className="grid w-full gap-2 text-sm">
        {fatias.map((f, i) => (
          <li key={f.nome} className="flex items-baseline justify-between gap-3">
            <span className="flex min-w-0 items-center gap-2">
              <span
                aria-hidden
                className="size-2.5 shrink-0 rounded-full ring-1 ring-border"
                style={{ background: `var(--chart-${i + 1})` }}
              />
              <span className="truncate">{f.nome}</span>
            </span>
            <span className="valor shrink-0">
              {formatarCentavos(f.total)}
              <span className="ml-2 inline-block w-10 text-right text-muted-foreground">
                {percentual(f.total, soma)}%
              </span>
            </span>
          </li>
        ))}
      </ul>
    </div>
  )
}
