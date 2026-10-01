import { FORMAS } from "@/features/dividas/rotulos"
import type { ResumoAdmin } from "@/lib/api/types"

/** Dívidas por forma de pagamento, da mais usada à menos, em barras proporcionais à maior. */
export function FormasPagamento({ formas }: { formas: ResumoAdmin["dividas_por_forma"] }) {
  const maior = Math.max(...formas.map((f) => f.quantidade))
  const total = formas.reduce((soma, f) => soma + f.quantidade, 0)

  if (total === 0) {
    return <p className="py-10 text-center text-sm text-muted-foreground">Nenhuma dívida cadastrada ainda.</p>
  }

  return (
    <ol className="flex flex-col gap-4">
      {formas.map((f) => (
        <li key={f.forma}>
          <div className="mb-1.5 flex items-baseline justify-between gap-2 text-sm">
            <span>{FORMAS[f.forma]}</span>
            <span className="valor text-muted-foreground">
              {f.quantidade} · {Math.round((f.quantidade / total) * 100)}%
            </span>
          </div>
          <div className="h-2 rounded-full bg-muted" aria-hidden>
            <div
              className="h-full rounded-full bg-foreground"
              style={{ width: `${maior ? (f.quantidade / maior) * 100 : 0}%` }}
            />
          </div>
        </li>
      ))}
    </ol>
  )
}
