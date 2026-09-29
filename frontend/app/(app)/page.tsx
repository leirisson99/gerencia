import type { Metadata } from "next"
import Link from "next/link"
import { cn } from "cn"

import { BarraProgresso } from "@/components/dados/barra-progresso"
import { Button } from "@/components/ui/button"
import { periodoCiclo } from "@/features/ciclo/navegacao-ciclo"
import { Bloco, Indicador } from "@/features/dashboard/bloco"
import { ListaLancamentos } from "@/features/lancamentos/lista-lancamentos"
import { NovoLancamento } from "@/features/lancamentos/novo-lancamento"
import { TotaisPorCategoria } from "@/features/resumo/totais-por-categoria"
import {
  listarCartelas,
  listarCategorias,
  listarLancamentosDoCiclo,
  obterCiclo,
  obterResumo,
  obterSugestaoSalario,
} from "@/lib/api/server"
import { acharSalario } from "@/lib/categorias"
import { diasEntre, formatarCentavos, hojeSaoPaulo } from "@/lib/format"

export const metadata: Metadata = { title: "Dashboard" }

const ULTIMOS = 8

/** Página inicial: quanto entrou, para onde foi e quanto sobrou no ciclo atual, na largura toda. */
export default async function DashboardPage() {
  const [ciclo, categorias, sugestaoSalario] = await Promise.all([
    obterCiclo(),
    listarCategorias(),
    obterSugestaoSalario(),
  ])

  if (!ciclo) {
    return (
      <section aria-labelledby="dashboard-titulo" className="max-w-180">
        <h1 id="dashboard-titulo" className="text-title">
          Dashboard
        </h1>
        <p className="mt-4 max-w-[52ch] text-muted-foreground">
          Ainda não há ciclo. Lance o salário para abrir o primeiro e acompanhar tudo por aqui.
        </p>
        <NovoLancamento
          className="mt-8"
          categorias={categorias}
          sugestaoSalario={sugestaoSalario}
          categoriaInicial={acharSalario(categorias)}
        >
          Lançar salário
        </NovoLancamento>
      </section>
    )
  }

  const [lancamentos, resumo, cartelas] = await Promise.all([
    listarLancamentosDoCiclo(ciclo.inicio),
    obterResumo(ciclo.inicio),
    listarCartelas(),
  ])
  const realizados = lancamentos.filter((l) => l.status === "realizado")
  const previstos = lancamentos.filter((l) => l.status === "previsto")
  const ultimos = realizados.slice(-ULTIMOS).reverse()
  const diaDoCiclo = diasEntre(ciclo.inicio, hojeSaoPaulo()) + 1

  return (
    <section aria-labelledby="dashboard-titulo">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 id="dashboard-titulo" className="text-title">
            Dashboard
          </h1>
          <p className="valor mt-2 text-muted-foreground">Ciclo atual · {periodoCiclo(ciclo)}</p>
        </div>
        <NovoLancamento categorias={categorias} sugestaoSalario={sugestaoSalario} />
      </div>

      <div className="mt-10 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Bloco titulo="Saldo do ciclo" className="sm:col-span-2 xl:col-span-1">
          <Indicador
            valor={formatarCentavos(resumo.saldo)}
            className={cn("text-display", resumo.saldo < 0 && "text-saida")}
            legenda="Entradas menos saídas realizadas"
          />
        </Bloco>
        <Bloco titulo="Entradas">
          <Indicador valor={formatarCentavos(resumo.entradas)} />
        </Bloco>
        <Bloco titulo="Saídas">
          <Indicador valor={formatarCentavos(resumo.saidas)} className="text-saida" />
        </Bloco>
        <Bloco titulo="Dia do ciclo">
          <Indicador
            valor={`${diaDoCiclo}º`}
            legenda={`${previstos.length} ${previstos.length === 1 ? "previsto pendente" : "previstos pendentes"}`}
          />
        </Bloco>
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-2 2xl:grid-cols-3">
        <Bloco titulo="Para onde foi">
          <TotaisPorCategoria
            totais={resumo.saidas_por_categoria}
            soma={resumo.saidas}
            tipo="saida"
            vazio="Nenhuma saída realizada neste ciclo."
          />
        </Bloco>
        <Bloco titulo="De onde veio">
          <TotaisPorCategoria
            totais={resumo.entradas_por_categoria}
            soma={resumo.entradas}
            tipo="entrada"
            vazio="Nenhuma entrada realizada neste ciclo."
          />
        </Bloco>
        <Bloco
          titulo="Poupança"
          className="lg:col-span-2 2xl:col-span-1"
          acao={
            <Button variant="link" size="sm" className="h-auto p-0" asChild>
              <Link href="/cartelas">Cartelas</Link>
            </Button>
          }
        >
          {cartelas.length === 0 ? (
            <p className="py-6 text-muted-foreground">
              Nenhuma cartela. O que sobrar do ciclo pode virar depósito numa meta.
            </p>
          ) : (
            <ul className="grid gap-4">
              {cartelas.map((c) => (
                <li key={c.id}>
                  <Link href={`/cartelas/${c.id}`} className="block hover:opacity-80">
                    <div className="flex items-baseline justify-between gap-3 text-sm">
                      <span className="truncate">{c.nome}</span>
                      <span className="valor shrink-0">
                        {formatarCentavos(c.guardado)}
                        <span className="text-muted-foreground"> de {formatarCentavos(c.meta)}</span>
                      </span>
                    </div>
                    <BarraProgresso valor={c.guardado} total={c.meta} className="mt-1.5" />
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </Bloco>
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <Bloco
          titulo="Últimos lançamentos"
          acao={
            <Button variant="link" size="sm" className="h-auto p-0" asChild>
              <Link href="/lancamentos">Ver todos</Link>
            </Button>
          }
        >
          <ListaLancamentos
            lancamentos={ultimos}
            categorias={categorias}
            sugestaoSalario={sugestaoSalario}
          />
        </Bloco>
        <Bloco titulo="Previstos do ciclo">
          <ListaLancamentos
            lancamentos={previstos}
            categorias={categorias}
            sugestaoSalario={sugestaoSalario}
            vazio="Nada previsto neste ciclo."
          />
        </Bloco>
      </div>
    </section>
  )
}
