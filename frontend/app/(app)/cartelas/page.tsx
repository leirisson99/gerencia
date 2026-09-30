import type { Metadata } from "next"

import { PageHeader } from "@/components/layout/page-header"
import { CartaoCartela } from "@/features/cartelas/cartao-cartela"
import { NovaCartela } from "@/features/cartelas/nova-cartela"
import { listarCartelas } from "@/lib/api/server"
import type { Cartela } from "@/lib/api/types"
import { formatarCentavos } from "@/lib/format"

export const metadata: Metadata = { title: "Cartelas" }

export default async function CartelasPage() {
  const cartelas = await listarCartelas()
  return (
    <>
      <div className="flex items-start justify-between gap-4 md:flex-wrap">
        <PageHeader
          titulo="Cartelas"
          descricao="Metas de poupança sem prazo. O que sobra do ciclo vira depósito numa casa."
        />
        <NovaCartela />
      </div>
      {cartelas.length === 0 ? (
        <p className="border-t py-8 text-muted-foreground">
          Nenhuma cartela. Crie uma meta, como uma viagem ou uma reserva, e vá marcando as casas
          conforme guardar.
        </p>
      ) : (
        <>
          <TotalGuardado cartelas={cartelas} />
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {cartelas.map((c) => (
              <CartaoCartela key={c.id} cartela={c} />
            ))}
          </div>
        </>
      )}
    </>
  )
}

/** Celular: soma de todas as cartelas em destaque antes da lista. */
function TotalGuardado({ cartelas }: { cartelas: Cartela[] }) {
  const guardado = cartelas.reduce((soma, c) => soma + c.guardado, 0)
  const meta = cartelas.reduce((soma, c) => soma + c.meta, 0)
  return (
    <section
      aria-label="Total guardado"
      className="mb-4 rounded-3xl bg-primary p-5 text-primary-foreground md:hidden"
    >
      <p className="text-sm opacity-70">Guardado nas cartelas</p>
      <p className="valor mt-1 text-[2.25rem] leading-none font-semibold tracking-tight">
        {formatarCentavos(guardado)}
      </p>
      <p className="valor mt-2 text-xs opacity-70">de {formatarCentavos(meta)} em metas</p>
      <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-primary-foreground/15">
        <div
          className="h-full rounded-full bg-primary-foreground"
          style={{ width: `${meta > 0 ? Math.min(100, (guardado / meta) * 100) : 0}%` }}
        />
      </div>
    </section>
  )
}
