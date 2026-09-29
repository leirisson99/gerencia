import { OctagonAlertIcon, TriangleAlertIcon } from "lucide-react"
import { cn } from "cn"

import type { SituacaoLimite, TotalCategoria } from "@/lib/api/types"
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
 * Categoria com limite vira medidor (usado ÷ limite) com a situação em ícone e texto.
 * Cada linha traz nome e valores escritos: a lista é também a tabela do gráfico.
 */
export function TotaisPorCategoria({ totais, soma, tipo, vazio }: Props) {
  if (totais.length === 0) return <p className="py-6 text-muted-foreground">{vazio}</p>
  const maior = Math.max(...totais.map((t) => t.total))

  return (
    <ul className="grid gap-4">
      {totais.map((t) => {
        const limite = t.situacao !== null ? t.limite : null
        // Proporções só para desenhar e rotular; os valores em centavos vêm prontos da API.
        const largura =
          limite !== null
            ? Math.min((t.total / limite) * 100, 100)
            : maior > 0
              ? (t.total / maior) * 100
              : 0
        const percentual = soma > 0 ? Math.round((t.total * 100) / soma) : 0
        return (
          <li key={t.categoria_id}>
            <div className="flex items-baseline justify-between gap-3 text-sm">
              <span className="flex min-w-0 items-baseline gap-2">
                <span className="truncate">{t.nome}</span>
                {t.situacao !== null && <Situacao situacao={t.situacao} />}
              </span>
              <span className="valor shrink-0">
                {formatarCentavos(t.total)}
                {limite !== null ? (
                  <span className="text-muted-foreground"> de {formatarCentavos(limite)}</span>
                ) : (
                  <span className="ml-2 inline-block w-10 text-right text-muted-foreground">
                    {percentual}%
                  </span>
                )}
              </span>
            </div>
            <div
              className={cn("mt-1.5 h-2 rounded-full", tipo === "saida" ? "bg-saida/10" : "bg-foreground/10")}
              aria-hidden
            >
              <div
                className={cn("h-full rounded-full", tipo === "saida" ? "bg-saida" : "bg-foreground")}
                style={{ width: `${t.total > 0 ? Math.max(largura, 1) : 0}%` }}
              />
            </div>
          </li>
        )
      })}
    </ul>
  )
}

/** Situação do limite: sempre ícone + texto, nunca só cor. "ok" não mostra nada. */
function Situacao({ situacao }: { situacao: SituacaoLimite }) {
  if (situacao === "ok") return null
  const estourado = situacao === "estourado"
  const Icone = estourado ? OctagonAlertIcon : TriangleAlertIcon
  return (
    <span
      className={cn(
        "inline-flex shrink-0 items-center gap-1 text-xs font-medium",
        estourado ? "text-saida" : "text-foreground"
      )}
    >
      <Icone className="size-3.5" aria-hidden />
      {estourado ? "Estourado" : "Atenção"}
    </span>
  )
}
