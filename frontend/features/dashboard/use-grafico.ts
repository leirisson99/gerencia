"use client"

import { useEffect, type DependencyList, type RefObject } from "react"
import { Chart, type ChartConfiguration } from "chart.js"

/** Valor de um token do tema (`--card`, `--chart-1`…) no modo em vigor. */
export function token(nome: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(nome).trim()
}

/**
 * Cria o gráfico no canvas e o refaz quando o sistema troca entre claro e escuro, porque o canvas
 * não acompanha as variáveis CSS sozinho. `montar` lê os tokens na hora; devolve `null` sem dados.
 */
export function useGrafico(
  canvas: RefObject<HTMLCanvasElement | null>,
  montar: () => ChartConfiguration | null,
  deps: DependencyList
) {
  useEffect(() => {
    if (!canvas.current) return
    const elemento = canvas.current
    Chart.defaults.font.family = getComputedStyle(document.body).fontFamily
    let grafico: Chart | null = null
    const desenhar = () => {
      grafico?.destroy()
      Chart.defaults.color = token("--muted-foreground")
      const config = montar()
      grafico = config ? new Chart(elemento, config) : null
    }
    desenhar()

    const midia = window.matchMedia("(prefers-color-scheme: dark)")
    midia.addEventListener("change", desenhar)
    return () => {
      midia.removeEventListener("change", desenhar)
      grafico?.destroy()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)
}
