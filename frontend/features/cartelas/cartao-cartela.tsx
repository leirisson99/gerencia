import Link from "next/link"
import { CheckCircle2Icon } from "lucide-react"

import { BarraProgresso } from "@/components/dados/barra-progresso"
import type { Cartela } from "@/lib/api/types"
import { formatarCentavos } from "@/lib/format"

/** Resumo de uma cartela na lista; leva à grade de casas. */
export function CartaoCartela({ cartela }: { cartela: Cartela }) {
  const completa = cartela.falta === 0
  return (
    <Link
      href={`/cartelas/${cartela.id}`}
      className="block rounded-lg border p-5 transition-colors hover:bg-muted/60"
    >
      <div className="flex items-start justify-between gap-3">
        <p className="min-w-0 truncate font-medium">{cartela.nome}</p>
        {completa ? (
          <span className="flex shrink-0 items-center gap-1 text-sm text-muted-foreground">
            <CheckCircle2Icon className="size-4" aria-hidden />
            Completa
          </span>
        ) : (
          <span className="valor shrink-0 text-sm text-muted-foreground">{cartela.percentual}%</span>
        )}
      </div>
      <p className="valor mt-4 text-xl font-semibold">
        {formatarCentavos(cartela.guardado)}
        <span className="ml-2 text-sm font-normal text-muted-foreground">
          de {formatarCentavos(cartela.meta)}
        </span>
      </p>
      <div className="mt-3">
        <BarraProgresso valor={cartela.guardado} total={cartela.meta} />
      </div>
      {!completa && (
        <p className="valor mt-2 text-sm text-muted-foreground">
          faltam {formatarCentavos(cartela.falta)}
          {cartela.maior_casa_livre !== null &&
            ` · maior casa livre ${formatarCentavos(cartela.maior_casa_livre)}`}
        </p>
      )}
    </Link>
  )
}
