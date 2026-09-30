import Link from "next/link"
import { CheckCircle2Icon } from "lucide-react"

import type { Cartela } from "@/lib/api/types"
import { formatarCentavos } from "@/lib/format"
import { MiniCartela } from "./mini-cartela"

/** Resumo de uma cartela na lista: quanto já guardou e a cartela em miniatura. */
export function CartaoCartela({ cartela }: { cartela: Cartela }) {
  const completa = cartela.falta === 0
  const depositadas = cartela.casas.filter((c) => c.depositado_em !== null).length

  return (
    <Link
      href={`/cartelas/${cartela.id}`}
      className="group flex flex-col rounded-2xl border p-4 transition-colors active:bg-muted/60 md:rounded-lg md:p-5 hover:border-foreground/40 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
    >
      <div className="flex items-baseline justify-between gap-3">
        <h2 className="min-w-0 truncate text-base font-medium">{cartela.nome}</h2>
        {completa ? (
          <span className="flex shrink-0 items-center gap-1 text-sm font-medium">
            <CheckCircle2Icon className="size-4" aria-hidden />
            Completa
          </span>
        ) : (
          <span className="valor shrink-0 text-sm text-muted-foreground">{cartela.percentual}%</span>
        )}
      </div>

      <p className="valor mt-3 text-title">{formatarCentavos(cartela.guardado)}</p>
      <p className="valor text-sm text-muted-foreground">de {formatarCentavos(cartela.meta)}</p>

      <MiniCartela cartela={cartela} className="mt-5" />

      <p className="valor mt-4 text-sm text-muted-foreground">
        {depositadas} de {cartela.casas.length} casas
        {!completa && ` · faltam ${formatarCentavos(cartela.falta)}`}
      </p>
    </Link>
  )
}
