import type { Metadata } from "next"
import Link from "next/link"
import { notFound } from "next/navigation"
import { ArrowLeftIcon, CheckCircle2Icon } from "lucide-react"

import { Button } from "@/components/ui/button"
import { GradeCasas } from "@/features/cartelas/grade-casas"
import { obterCartela } from "@/lib/api/server"
import { formatarCentavos } from "@/lib/format"

export const metadata: Metadata = { title: "Cartela" }

/** Uma cartela: quanto já guardou e a grade de casas para marcar e desmarcar depósitos. */
export default async function CartelaPage({ params }: PageProps<"/cartelas/[id]">) {
  const { id } = await params
  if (!/^\d+$/.test(id)) notFound()
  const cartela = await obterCartela(Number(id))
  if (!cartela) notFound()

  const depositadas = cartela.casas.filter((c) => c.depositado_em !== null).length
  const completa = cartela.falta === 0

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

      <div className="mt-8 max-w-3xl">
        <p className="valor flex flex-wrap items-baseline gap-x-3">
          <span className="text-display">{formatarCentavos(cartela.guardado)}</span>
          <span className="text-xl text-muted-foreground">de {formatarCentavos(cartela.meta)}</span>
        </p>

        <div className="mt-5 flex items-center gap-4">
          {/* Medidor: trilho num tom mais claro da mesma cor. */}
          <div className="h-3 flex-1 rounded-full bg-foreground/10" aria-hidden>
            <div
              className="h-full rounded-full bg-foreground"
              style={{ width: `${Math.min(cartela.percentual, 100)}%` }}
            />
          </div>
          <span className="valor w-12 text-right font-semibold">{cartela.percentual}%</span>
        </div>

        <dl className="valor mt-4 flex flex-wrap gap-x-8 gap-y-2 text-sm">
          {completa ? (
            <div className="flex items-center gap-1.5 font-medium">
              <CheckCircle2Icon className="size-4" aria-hidden />
              <dt className="sr-only">Situação</dt>
              <dd>Meta completa</dd>
            </div>
          ) : (
            <div className="flex gap-2">
              <dt className="text-muted-foreground">Faltam</dt>
              <dd className="font-medium">{formatarCentavos(cartela.falta)}</dd>
            </div>
          )}
          <div className="flex gap-2">
            <dt className="text-muted-foreground">Casas</dt>
            <dd className="font-medium">
              {depositadas} de {cartela.casas.length}
            </dd>
          </div>
          {cartela.maior_casa_livre !== null && (
            <div className="flex gap-2">
              <dt className="text-muted-foreground">Maior casa livre</dt>
              <dd className="font-medium">{formatarCentavos(cartela.maior_casa_livre)}</dd>
            </div>
          )}
        </dl>
      </div>

      <div className="mt-12 mb-4 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-xl">Casas</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Guardou o valor de uma casa? Toque nela para marcar o depósito.
          </p>
        </div>
        <Legenda />
      </div>
      <GradeCasas cartela={cartela} />
    </section>
  )
}

function Legenda() {
  return (
    <ul className="flex gap-4 text-xs text-muted-foreground" aria-label="Legenda">
      <li className="flex items-center gap-1.5">
        <span className="size-3 rounded-[3px] bg-foreground" aria-hidden />
        depositada
      </li>
      <li className="flex items-center gap-1.5">
        <span className="size-3 rounded-[3px] border border-foreground/30" aria-hidden />
        livre
      </li>
      <li className="flex items-center gap-1.5">
        <span className="size-3 rounded-[3px] border border-dashed border-foreground/60" aria-hidden />
        ajuste
      </li>
    </ul>
  )
}
