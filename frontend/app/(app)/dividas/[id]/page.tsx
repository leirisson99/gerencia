import type { Metadata } from "next"
import Link from "next/link"
import { notFound } from "next/navigation"
import { ArrowLeftIcon } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Bloco, Indicador } from "@/features/dashboard/bloco"
import { BarraProgresso } from "@/features/dividas/cartao-divida"
import { DIRECOES, FORMAS, rotuloConfirmarParcela } from "@/features/dividas/rotulos"
import { ListaLancamentos } from "@/features/lancamentos/lista-lancamentos"
import { listarCategorias, obterDivida, obterSugestaoSalario } from "@/lib/api/server"
import { formatarCentavos, formatarData } from "@/lib/format"

export const metadata: Metadata = { title: "Dívida" }

/** Uma dívida com suas parcelas; cada parcela prevista pode ser marcada como paga ou recebida. */
export default async function DividaPage({ params }: PageProps<"/dividas/[id]">) {
  const { id } = await params
  if (!/^\d+$/.test(id)) notFound()

  const [divida, categorias, sugestaoSalario] = await Promise.all([
    obterDivida(Number(id)),
    listarCategorias(),
    obterSugestaoSalario(),
  ])
  if (!divida) notFound()

  return (
    <section aria-labelledby="divida-titulo">
      <Button variant="ghost" size="sm" className="-ml-2 mb-4" asChild>
        <Link href="/dividas">
          <ArrowLeftIcon aria-hidden />
          Dívidas
        </Link>
      </Button>

      <h1 id="divida-titulo" className="text-title">
        {divida.descricao}
      </h1>
      <p className="mt-2 text-muted-foreground">
        {DIRECOES[divida.direcao]} · {divida.pessoa} · {FORMAS[divida.forma_pagamento]} · vence todo dia{" "}
        {divida.dia_vencimento} · desde {formatarData(divida.data_inicio)}
      </p>

      <div className="mt-8 grid gap-4 sm:grid-cols-3">
        <Bloco titulo="Total">
          <Indicador
            valor={formatarCentavos(divida.valor_total)}
            legenda={`${divida.parcelas} ${divida.parcelas === 1 ? "parcela" : "parcelas"}`}
          />
        </Bloco>
        <Bloco titulo={divida.direcao === "devo" ? "Pago" : "Recebido"}>
          <Indicador
            valor={formatarCentavos(divida.valor_pago)}
            legenda={`${divida.parcelas_pagas} de ${divida.parcelas}`}
          />
          <div className="mt-3">
            <BarraProgresso divida={divida} />
          </div>
        </Bloco>
        <Bloco titulo="Falta">
          <Indicador
            valor={divida.quitada ? "Quitada" : formatarCentavos(divida.valor_restante)}
          />
        </Bloco>
      </div>

      <h2 className="mt-12 mb-3 text-sm font-medium text-muted-foreground">Parcelas</h2>
      <ListaLancamentos
        lancamentos={divida.lancamentos}
        categorias={categorias}
        sugestaoSalario={sugestaoSalario}
        rotuloConfirmar={rotuloConfirmarParcela(divida.direcao)}
      />
    </section>
  )
}
