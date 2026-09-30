import type { Metadata } from "next"
import Link from "next/link"
import { redirect } from "next/navigation"
import { ChevronLeftIcon, ChevronRightIcon } from "lucide-react"

import { Button } from "@/components/ui/button"
import { CalendarioMes } from "@/features/calendario/calendario-mes"
import { limitesDoMes, mesValido, mesVizinho } from "@/features/calendario/datas"
import { NovoLancamento } from "@/features/lancamentos/novo-lancamento"
import {
  listarCategorias,
  listarLancamentosDoPeriodo,
  obterSugestaoSalario,
} from "@/lib/api/server"
import { formatarMes, hojeSaoPaulo } from "@/lib/format"

export const metadata: Metadata = { title: "Calendário" }

/** Pagamentos do mês (`?mes=YYYY-MM`, padrão o mês atual): o que venceu, o que vence e o que foi pago. */
export default async function CalendarioPage({ searchParams }: PageProps<"/calendario">) {
  const { mes: param } = await searchParams
  const hoje = hojeSaoPaulo()
  const mes = typeof param === "string" ? param : hoje.slice(0, 7)
  if (!mesValido(mes)) redirect("/calendario")

  const { inicio, fim } = limitesDoMes(mes)
  const [lancamentos, categorias, sugestaoSalario] = await Promise.all([
    listarLancamentosDoPeriodo(inicio, fim),
    listarCategorias(),
    obterSugestaoSalario(),
  ])
  const [nomeDoMes, ano] = formatarMes(mes).split(" de ")

  return (
    <section aria-labelledby="calendario-titulo">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <h1 id="calendario-titulo" className="text-display">
          <span className="capitalize">{nomeDoMes}</span>{" "}
          <span className="font-normal text-muted-foreground">{ano}</span>
        </h1>
        <div className="flex items-center gap-3">
          <nav aria-label="Meses" className="flex items-center gap-1">
            <Button variant="outline" size="icon" asChild>
              <Link href={`/calendario?mes=${mesVizinho(mes, -1)}`} aria-label="Mês anterior" title="Mês anterior">
                <ChevronLeftIcon aria-hidden />
              </Link>
            </Button>
            <Button variant="outline" asChild>
              <Link href="/calendario" aria-current={mes === hoje.slice(0, 7) ? "date" : undefined}>
                Hoje
              </Link>
            </Button>
            <Button variant="outline" size="icon" asChild>
              <Link href={`/calendario?mes=${mesVizinho(mes, 1)}`} aria-label="Próximo mês" title="Próximo mês">
                <ChevronRightIcon aria-hidden />
              </Link>
            </Button>
          </nav>
          <NovoLancamento categorias={categorias} sugestaoSalario={sugestaoSalario} />
        </div>
      </div>

      <CalendarioMes
        mes={mes}
        hoje={hoje}
        saidas={lancamentos.filter((l) => l.tipo === "saida")}
        categorias={categorias}
        sugestaoSalario={sugestaoSalario}
      />
    </section>
  )
}
