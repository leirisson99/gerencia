import type { Metadata } from "next"
import Link from "next/link"
import { notFound } from "next/navigation"
import { ArrowLeftIcon } from "lucide-react"

import { BarraProgresso } from "@/components/dados/barra-progresso"
import { Button } from "@/components/ui/button"
import { GradeCasas } from "@/features/cartelas/grade-casas"
import { Bloco, Indicador } from "@/features/dashboard/bloco"
import { obterCartela } from "@/lib/api/server"
import { formatarCentavos } from "@/lib/format"

export const metadata: Metadata = { title: "Cartela" }

/** Uma cartela: progresso no topo e a grade de casas para marcar e desmarcar depósitos. */
export default async function CartelaPage({ params }: PageProps<"/cartelas/[id]">) {
  const { id } = await params
  if (!/^\d+$/.test(id)) notFound()
  const cartela = await obterCartela(Number(id))
  if (!cartela) notFound()

  const depositadas = cartela.casas.filter((c) => c.depositado_em !== null).length

  return (
    <section aria-labelledby="cartela-titulo">
      <Button variant="ghost" size="sm" className="-ml-2 mb-4" asChild>
        <Link href="/cartelas">
          <ArrowLeftIcon aria-hidden />
          Cartelas
        </Link>
      </Button>
      <h1 id="cartela-titulo" className="text-title">
        {cartela.nome}
      </h1>
      <p className="valor mt-2 text-muted-foreground">
        Meta {formatarCentavos(cartela.meta)} · casas a partir de {formatarCentavos(cartela.valor_base)}
      </p>

      <div className="mt-8 grid gap-4 sm:grid-cols-3">
        <Bloco titulo="Guardado">
          <Indicador valor={formatarCentavos(cartela.guardado)} legenda={`${depositadas} de ${cartela.casas.length} casas`} />
          <div className="mt-3">
            <BarraProgresso valor={cartela.guardado} total={cartela.meta} />
          </div>
        </Bloco>
        <Bloco titulo="Falta">
          <Indicador
            valor={cartela.falta === 0 ? "Completa" : formatarCentavos(cartela.falta)}
            legenda={
              cartela.maior_casa_livre !== null
                ? `Maior casa livre: ${formatarCentavos(cartela.maior_casa_livre)}`
                : undefined
            }
          />
        </Bloco>
        <Bloco titulo="Progresso">
          <Indicador valor={`${cartela.percentual}%`} />
        </Bloco>
      </div>

      <h2 className="mt-12 mb-1 text-sm font-medium text-muted-foreground">Casas</h2>
      <p className="mb-4 text-sm text-muted-foreground">
        Toque numa casa livre quando guardar o valor dela. Toque de novo para desfazer.
      </p>
      <GradeCasas cartela={cartela} />
    </section>
  )
}
