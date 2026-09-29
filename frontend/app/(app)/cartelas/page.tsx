import type { Metadata } from "next"

import { PageHeader } from "@/components/layout/page-header"
import { CartaoCartela } from "@/features/cartelas/cartao-cartela"
import { NovaCartela } from "@/features/cartelas/nova-cartela"
import { listarCartelas } from "@/lib/api/server"

export const metadata: Metadata = { title: "Cartelas" }

export default async function CartelasPage() {
  const cartelas = await listarCartelas()
  return (
    <>
      <div className="flex flex-wrap items-start justify-between gap-4">
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
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {cartelas.map((c) => (
            <CartaoCartela key={c.id} cartela={c} />
          ))}
        </div>
      )}
    </>
  )
}
