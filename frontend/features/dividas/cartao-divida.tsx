import Link from "next/link"
import { CheckCircle2Icon } from "lucide-react"

import { BarraProgresso } from "@/components/dados/barra-progresso"
import type { Divida } from "@/lib/api/types"
import { formatarCentavos } from "@/lib/format"
import { DIRECOES } from "./rotulos"

/** Resumo de uma dívida na lista; leva ao detalhe com as parcelas. */
export function CartaoDivida({ divida }: { divida: Divida }) {
  return (
    <Link
      href={`/dividas/${divida.id}`}
      className="block rounded-lg border p-5 transition-colors hover:bg-muted/60"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="truncate font-medium">{divida.descricao}</p>
          <p className="truncate text-sm text-muted-foreground">
            {DIRECOES[divida.direcao]} · {divida.pessoa}
          </p>
        </div>
        {divida.quitada && (
          <span className="flex shrink-0 items-center gap-1 text-sm text-muted-foreground">
            <CheckCircle2Icon className="size-4" aria-hidden />
            Quitada
          </span>
        )}
      </div>
      <p className="valor mt-4 text-xl font-semibold">{formatarCentavos(divida.valor_total)}</p>
      <div className="mt-3">
        <BarraProgresso valor={divida.valor_pago} total={divida.valor_total} />
      </div>
      <div className="valor mt-2 flex justify-between gap-3 text-sm text-muted-foreground">
        <span>
          {divida.parcelas_pagas} de {divida.parcelas} {divida.parcelas === 1 ? "parcela" : "parcelas"}
        </span>
        {!divida.quitada && <span>faltam {formatarCentavos(divida.valor_restante)}</span>}
      </div>
    </Link>
  )
}
