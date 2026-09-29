import { cn } from "cn"

import type { TotalCategoria } from "@/lib/api/types"
import { formatarCentavos } from "@/lib/format"

type Props = {
  totais: TotalCategoria[]
  /** Soma de todos os totais, para o percentual de cada categoria. */
  soma: number
  /** Saídas usam a cor de saída; entradas, a cor do texto. */
  tipo: "entrada" | "saida"
  vazio: string
}

/**
 * Barras horizontais de uma série só, na ordem da API (maior total primeiro).
 * Cada linha traz nome, valor e percentual escritos: a lista é também a tabela do gráfico.
 */
export function TotaisPorCategoria({ totais, soma, tipo, vazio }: Props) {
  if (totais.length === 0) return <p className="py-6 text-muted-foreground">{vazio}</p>
  const maior = totais[0].total

  return (
    <ul className="grid gap-4">
      {totais.map((t) => {
        // Proporções só para desenhar e rotular; os valores em centavos vêm prontos da API.
        const largura = maior > 0 ? (t.total / maior) * 100 : 0
        const percentual = soma > 0 ? Math.round((t.total * 100) / soma) : 0
        return (
          <li key={t.categoria_id} title={`${t.nome}: ${formatarCentavos(t.total)} (${percentual}%)`}>
            <div className="flex items-baseline justify-between gap-3 text-sm">
              <span className="truncate">{t.nome}</span>
              <span className="valor shrink-0">
                {formatarCentavos(t.total)}
                <span className="ml-2 inline-block w-10 text-right text-muted-foreground">{percentual}%</span>
              </span>
            </div>
            <div
              className={cn("mt-1.5 h-2 rounded-full", tipo === "saida" ? "bg-saida/10" : "bg-foreground/10")}
              aria-hidden
            >
              <div
                className={cn("h-full rounded-full", tipo === "saida" ? "bg-saida" : "bg-foreground")}
                style={{ width: `${Math.max(largura, 1)}%` }}
              />
            </div>
          </li>
        )
      })}
    </ul>
  )
}
