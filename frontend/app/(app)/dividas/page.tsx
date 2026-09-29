import type { Metadata } from "next"

import { PageHeader } from "@/components/layout/page-header"
import { CartaoDivida } from "@/features/dividas/cartao-divida"
import { NovaDivida } from "@/features/dividas/nova-divida"
import { listarCategorias, listarDividas } from "@/lib/api/server"

export const metadata: Metadata = { title: "Dívidas" }

export default async function DividasPage() {
  const [dividas, categorias] = await Promise.all([listarDividas(), listarCategorias()])
  const abertas = dividas.filter((d) => !d.quitada)
  const quitadas = dividas.filter((d) => d.quitada)

  return (
    <>
      <div className="flex flex-wrap items-start justify-between gap-4">
        <PageHeader
          titulo="Dívidas"
          descricao="O que você deve e o que te devem, parcela por parcela."
        />
        <NovaDivida categorias={categorias} />
      </div>

      {dividas.length === 0 ? (
        <p className="border-t py-8 text-muted-foreground">
          Nenhuma dívida. Cadastre uma compra parcelada ou um empréstimo para as parcelas aparecerem
          como previstas em cada ciclo.
        </p>
      ) : (
        <>
          <Grade titulo="Em aberto" dividas={abertas} vazio="Nenhuma dívida em aberto." />
          {quitadas.length > 0 && <Grade titulo="Quitadas" dividas={quitadas} />}
        </>
      )}
    </>
  )
}

function Grade({
  titulo,
  dividas,
  vazio,
}: {
  titulo: string
  dividas: Awaited<ReturnType<typeof listarDividas>>
  vazio?: string
}) {
  return (
    <section className="mb-10">
      <h2 className="mb-3 text-sm font-medium text-muted-foreground">{titulo}</h2>
      {dividas.length === 0 ? (
        <p className="text-muted-foreground">{vazio}</p>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {dividas.map((d) => (
            <CartaoDivida key={d.id} divida={d} />
          ))}
        </div>
      )}
    </section>
  )
}
