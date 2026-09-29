import type { Metadata } from "next"
import { redirect } from "next/navigation"
import { cn } from "cn"

import { NavegacaoCiclo, periodoCiclo } from "@/features/ciclo/navegacao-ciclo"
import { ListaLancamentos } from "@/features/lancamentos/lista-lancamentos"
import { NovoLancamento } from "@/features/lancamentos/novo-lancamento"
import {
  listarCategorias,
  listarLancamentosDoCiclo,
  obterCiclo,
  obterResumo,
  obterSugestaoSalario,
} from "@/lib/api/server"
import { acharSalario } from "@/lib/categorias"
import { formatarCentavos } from "@/lib/format"

export const metadata: Metadata = { title: "Lançamentos" }

const DATA_ISO = /^\d{4}-\d{2}-\d{2}$/

/** Ciclo atual, ou o de `?ciclo=YYYY-MM-DD`, com seus lançamentos. */
export default async function LancamentosPage({ searchParams }: PageProps<"/lancamentos">) {
  const { ciclo: param } = await searchParams
  const dataCiclo = typeof param === "string" && DATA_ISO.test(param) ? param : undefined
  if (param !== undefined && !dataCiclo) redirect("/lancamentos")

  const [ciclo, categorias, sugestaoSalario] = await Promise.all([
    obterCiclo(dataCiclo),
    listarCategorias(),
    obterSugestaoSalario(),
  ])
  const salario = acharSalario(categorias)

  if (!ciclo) {
    // Data fora de qualquer ciclo: volta ao atual, que decide se há ciclo.
    if (dataCiclo) redirect("/lancamentos")
    return (
      <section aria-labelledby="ciclo-titulo">
        <h1 id="ciclo-titulo" className="text-title">
          Nenhum ciclo aberto
        </h1>
        <p className="valor mt-6 text-display text-muted-foreground/40" aria-hidden>
          {formatarCentavos(0)}
        </p>
        <p className="mt-6 max-w-[52ch] text-muted-foreground">
          O ciclo começa quando você lança o salário. A partir daí, cada gasto aparece aqui,
          separado por categoria, junto com quanto ainda sobra até o próximo salário.
        </p>
        <NovoLancamento
          className="mt-8"
          categorias={categorias}
          sugestaoSalario={sugestaoSalario}
          categoriaInicial={salario}
        >
          Lançar salário
        </NovoLancamento>
      </section>
    )
  }

  const [lancamentos, resumo] = await Promise.all([
    listarLancamentosDoCiclo(ciclo.inicio),
    obterResumo(ciclo.inicio),
  ])

  return (
    <section aria-labelledby="ciclo-titulo">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 id="ciclo-titulo" className="text-title">
            {ciclo.aberto ? "Ciclo atual" : "Ciclo encerrado"}
          </h1>
          <p className="valor mt-2 text-muted-foreground">{periodoCiclo(ciclo)}</p>
          <dl className="valor mt-4 flex flex-wrap gap-x-6 gap-y-1 text-sm">
            <div className="flex gap-2">
              <dt className="text-muted-foreground">Saldo</dt>
              <dd className={cn("font-medium", resumo.saldo < 0 && "text-saida")}>
                {formatarCentavos(resumo.saldo)}
              </dd>
            </div>
            <div className="flex gap-2">
              <dt className="text-muted-foreground">Entradas</dt>
              <dd>{formatarCentavos(resumo.entradas)}</dd>
            </div>
            <div className="flex gap-2">
              <dt className="text-muted-foreground">Saídas</dt>
              <dd className="text-saida">{formatarCentavos(resumo.saidas)}</dd>
            </div>
          </dl>
        </div>
        <div className="flex items-center gap-3">
          <NavegacaoCiclo ciclo={ciclo} />
          <NovoLancamento categorias={categorias} sugestaoSalario={sugestaoSalario} />
        </div>
      </div>

      <h2 className="mt-12 mb-3 text-sm font-medium text-muted-foreground">Lançamentos</h2>
      <ListaLancamentos
        lancamentos={lancamentos}
        categorias={categorias}
        sugestaoSalario={sugestaoSalario}
      />
    </section>
  )
}
