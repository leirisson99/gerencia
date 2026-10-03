import type { Metadata } from "next"
import type { ReactNode } from "react"
import { redirect } from "next/navigation"
import { cn } from "cn"

import {
  NavegacaoCiclo,
  NavegacaoCicloCompacta,
  periodoCiclo,
  tituloCiclo,
} from "@/features/ciclo/navegacao-ciclo"
import { FiltroLancamentos } from "@/features/lancamentos/filtro-lancamentos"
import { NovoLancamento } from "@/features/lancamentos/novo-lancamento"
import { DialogRetirada } from "@/features/retiradas/dialog-retirada"
import {
  listarCategorias,
  listarLancamentosDoCiclo,
  obterCiclo,
  obterResumo,
  obterSugestaoSalario,
  obterTipoRenda,
} from "@/lib/api/server"
import { obterCarteira } from "@/lib/carteira"
import { acharSalario } from "@/lib/categorias"
import { formatarCentavos } from "@/lib/format"
import { cicloPeloMes } from "@/lib/tipo-renda"

export const metadata: Metadata = { title: "Lançamentos" }

const DATA_ISO = /^\d{4}-\d{2}-\d{2}$/

/** Ciclo atual, ou o de `?ciclo=YYYY-MM-DD`, com seus lançamentos. Para o prestador, o mês. */
export default async function LancamentosPage({ searchParams }: PageProps<"/lancamentos">) {
  const { ciclo: param } = await searchParams
  const dataCiclo = typeof param === "string" && DATA_ISO.test(param) ? param : undefined
  if (param !== undefined && !dataCiclo) redirect("/lancamentos")

  const [ciclo, categorias, sugestaoSalario, tipoRenda, carteira] = await Promise.all([
    obterCiclo(dataCiclo),
    listarCategorias(),
    obterSugestaoSalario(),
    obterTipoRenda(),
    obterCarteira(),
  ])
  const salario = acharSalario(categorias)
  // A PJ conta sempre pelo mês, como o prestador.
  const mensal = cicloPeloMes(tipoRenda, carteira)

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
      {/* Celular: pílula de navegação do ciclo e três números em cartões. Lançar fica na barra inferior. */}
      <div className="md:hidden">
        <NavegacaoCicloCompacta ciclo={ciclo} mensal={mensal} />
        <dl className="valor mt-4 grid grid-cols-3 gap-2">
          <ResumoCartao titulo="Saldo" destaque>
            <span className={cn(resumo.saldo < 0 && "text-saida")}>
              {formatarCentavos(resumo.saldo)}
            </span>
          </ResumoCartao>
          <ResumoCartao titulo="Entradas">{formatarCentavos(resumo.entradas)}</ResumoCartao>
          <ResumoCartao titulo="Saídas">
            <span className="text-saida">{formatarCentavos(resumo.saidas)}</span>
          </ResumoCartao>
        </dl>
      </div>

      <div className="hidden flex-wrap items-start justify-between gap-4 md:flex">
        <div>
          <h1 id="ciclo-titulo" className="text-title">
            {tituloCiclo(ciclo, mensal)}
          </h1>
          <p className="valor mt-2 text-muted-foreground">{periodoCiclo(ciclo, mensal)}</p>
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
          <NavegacaoCiclo ciclo={ciclo} mensal={mensal} />
          <DialogRetirada />
          <NovoLancamento categorias={categorias} sugestaoSalario={sugestaoSalario} />
        </div>
      </div>

      <h2 className="mt-8 mb-3 font-semibold md:mt-12 md:text-sm md:font-medium md:text-muted-foreground">
        Lançamentos
      </h2>
      <FiltroLancamentos
        lancamentos={lancamentos}
        categorias={categorias}
        sugestaoSalario={sugestaoSalario}
      />
    </section>
  )
}

function ResumoCartao({
  titulo,
  destaque = false,
  children,
}: {
  titulo: string
  /** Fundo invertido para o saldo, o número que mais importa. */
  destaque?: boolean
  children: ReactNode
}) {
  return (
    <div
      className={cn(
        "min-w-0 rounded-2xl p-3",
        destaque ? "bg-primary text-primary-foreground" : "bg-muted"
      )}
    >
      <dt className={cn("text-xs", destaque ? "opacity-70" : "text-muted-foreground")}>{titulo}</dt>
      <dd className="mt-1 truncate text-sm font-semibold">{children}</dd>
    </div>
  )
}
