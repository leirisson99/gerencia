import type { Metadata } from "next"
import Link from "next/link"
import { cn } from "cn"

import { BarraProgresso } from "@/components/dados/barra-progresso"
import { Button } from "@/components/ui/button"
import { periodoCiclo, tituloCiclo } from "@/features/ciclo/navegacao-ciclo"
import { Atalhos, SaldoDestaque } from "@/features/dashboard/mobile"
import { Bloco, Indicador } from "@/features/dashboard/bloco"
import { GraficoPizza } from "@/features/dashboard/grafico-pizza"
import { GraficoEntradasSaidas, GraficoSaldo } from "@/features/dashboard/graficos"
import { saldoDiaADia, totaisPorPeriodo } from "@/features/dashboard/series"
import { ListaLancamentos } from "@/features/lancamentos/lista-lancamentos"
import { NovoLancamento } from "@/features/lancamentos/novo-lancamento"
import { TotaisPorCategoria } from "@/features/resumo/totais-por-categoria"
import {
  listarCartelas,
  listarCategorias,
  listarLancamentosDoCiclo,
  listarLancamentosDoPeriodo,
  obterCiclo,
  obterResumo,
  obterSugestaoSalario,
  obterTipoRenda,
} from "@/lib/api/server"
import type { ResumoCiclo } from "@/lib/api/types"
import { acharSalario } from "@/lib/categorias"
import { diasEntre, formatarCentavos, hojeSaoPaulo } from "@/lib/format"
import { ehPrestador, nomeCiclo } from "@/lib/tipo-renda"

export const metadata: Metadata = { title: "Dashboard" }

/** Teto da lista "Últimos lançamentos", que só mostra o mês atual. */
const ULTIMOS = 10

/** Quantos lançamentos as listas do dashboard mostram por vez. */
const POR_PAGINA = 5

/** Primeiro e último dia do mês de `hoje` (ISO). */
function mesDe(hoje: string): { inicio: string; fim: string } {
  const [ano, mes] = hoje.split("-").map(Number)
  const ultimoDia = new Date(Date.UTC(ano, mes, 0)).getUTCDate()
  const prefixo = hoje.slice(0, 7)
  return { inicio: `${prefixo}-01`, fim: `${prefixo}-${String(ultimoDia).padStart(2, "0")}` }
}

/** Quantos ciclos (ou meses) o gráfico de entradas e saídas mostra, contando o atual. */
const HISTORICO = 6

/** O resumo dado e os anteriores a ele, seguindo `ciclo.anterior`, até `quantos` no total. */
async function resumosAte(atual: ResumoCiclo, quantos: number): Promise<ResumoCiclo[]> {
  const resumos = [atual]
  while (resumos.length < quantos) {
    const anterior = resumos[resumos.length - 1].ciclo.anterior
    if (!anterior) break
    try {
      resumos.push(await obterResumo(anterior))
    } catch {
      break // Histórico é complemento: sem ele o gráfico só fica mais curto.
    }
  }
  return resumos
}

/**
 * Página inicial: quanto entrou, para onde foi e quanto sobrou no ciclo atual, na largura toda.
 * Para o prestador o ciclo é o mês, que sempre existe.
 */
export default async function DashboardPage() {
  const [ciclo, categorias, sugestaoSalario, tipoRenda] = await Promise.all([
    obterCiclo(),
    listarCategorias(),
    obterSugestaoSalario(),
    obterTipoRenda(),
  ])
  const mensal = ehPrestador(tipoRenda)
  const nome = nomeCiclo(tipoRenda)

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

  const hoje = hojeSaoPaulo()
  const mes = mesDe(hoje)
  const [lancamentos, resumo, cartelas, lancamentosDoMes] = await Promise.all([
    listarLancamentosDoCiclo(ciclo.inicio),
    obterResumo(ciclo.inicio),
    listarCartelas(),
    // Para o prestador o ciclo já é o mês; o CLT tem ciclo de salário a salário, que cruza meses.
    mensal ? null : listarLancamentosDoPeriodo(mes.inicio, mes.fim),
  ])
  const previstos = lancamentos.filter((l) => l.status === "previsto")
  const ultimos = (lancamentosDoMes ?? lancamentos)
    .filter((l) => l.status === "realizado" && l.data >= mes.inicio && l.data <= mes.fim)
    .slice(-ULTIMOS)
    .reverse()
  const historico = totaisPorPeriodo(await resumosAte(resumo, HISTORICO), mensal)
  const diaDoCiclo = diasEntre(ciclo.inicio, hoje) + 1
  const periodo = periodoCiclo(ciclo, mensal)
  const ateHoje = ciclo.fim && ciclo.fim < hoje ? ciclo.fim : hoje
  const pontosSaldo = saldoDiaADia(lancamentos, ciclo.inicio, ateHoje)
  const gasto = resumo.entradas > 0 ? Math.round((resumo.saidas * 100) / resumo.entradas) : null
  const comLimite = resumo.saidas_por_categoria.filter((t) => t.situacao !== null)
  const guardado = cartelas.reduce((s, c) => s + c.guardado, 0)
  const metaTotal = cartelas.reduce((s, c) => s + c.meta, 0)

  return (
    <section aria-labelledby="dashboard-titulo" className="flex flex-col md:block">
      <div className="flex flex-wrap items-start justify-between gap-4 max-md:sr-only">
        <div>
          <h1 id="dashboard-titulo" className="text-title">
            Dashboard
          </h1>
          <p className="valor mt-2 text-muted-foreground">
            {tituloCiclo(ciclo, mensal)} · {periodo}
          </p>
        </div>
        <NovoLancamento categorias={categorias} sugestaoSalario={sugestaoSalario} />
      </div>

      {/* Celular: saldo em destaque e atalhos, no lugar da grade de blocos. */}
      <div className="order-1 md:hidden">
        <SaldoDestaque
          saldo={resumo.saldo}
          entradas={resumo.entradas}
          saidas={resumo.saidas}
          periodo={periodo}
          diaDoCiclo={diaDoCiclo}
          nome={nome}
          guardado={guardado}
          categorias={categorias}
          sugestaoSalario={sugestaoSalario}
        />
        <Atalhos className="mt-6" />
      </div>

      {/* Desktop: o saldo é o primeiro olhar; entradas, saídas, poupança e o dia vêm em seguida, menores. */}
      <div className="mt-10 hidden gap-4 md:grid md:grid-cols-4 xl:grid-cols-[1.4fr_1fr_1fr_1fr_1fr]">
        <Bloco
          titulo={`Saldo do ${nome}`}
          className="bg-primary text-primary-foreground md:col-span-4 xl:col-span-1 [&_h2]:text-primary-foreground/70"
        >
          <Indicador
            valor={formatarCentavos(resumo.saldo)}
            className={cn("text-display", resumo.saldo < 0 && "text-saida")}
            legenda={<span className="text-primary-foreground/70">Entradas menos saídas realizadas</span>}
          />
        </Bloco>
        <Bloco titulo="Entradas">
          <Indicador valor={formatarCentavos(resumo.entradas)} />
        </Bloco>
        <Bloco titulo="Saídas">
          <Indicador
            valor={formatarCentavos(resumo.saidas)}
            className="text-saida"
            legenda={gasto !== null ? `${gasto}% do que entrou` : undefined}
          />
        </Bloco>
        <Bloco
          titulo="Poupança"
          acao={
            <Button variant="link" size="sm" className="h-auto p-0" asChild>
              <Link href="/cartelas">Cartelas</Link>
            </Button>
          }
        >
          <Indicador
            valor={formatarCentavos(guardado)}
            legenda={
              cartelas.length === 0
                ? "Nenhuma cartela criada"
                : `de ${formatarCentavos(metaTotal)} em ${cartelas.length} ${cartelas.length === 1 ? "cartela" : "cartelas"}`
            }
          />
        </Bloco>
        <Bloco titulo={`Dia do ${nome}`}>
          <Indicador
            valor={`${diaDoCiclo}º`}
            legenda={`${previstos.length} ${previstos.length === 1 ? "previsto pendente" : "previstos pendentes"}`}
          />
        </Bloco>
      </div>

      <div className="order-3 mt-4 grid gap-4 lg:grid-cols-3">
        <Bloco titulo={`Saldo ao longo do ${nome}`} className="lg:col-span-2">
          <GraficoSaldo
            pontos={pontosSaldo}
            rotulo={`Gráfico de linha do saldo acumulado por dia, ${periodo}`}
          />
        </Bloco>
        <Bloco titulo="Para onde foi">
          <GraficoPizza
            totais={resumo.saidas_por_categoria}
            soma={resumo.saidas}
            vazio={`Nenhuma saída realizada neste ${nome}.`}
            rotulo={`Gráfico de pizza das saídas do ${nome} por categoria`}
          />
          {comLimite.length > 0 && (
            <div className="mt-5 border-t pt-4">
              <h3 className="mb-3 text-sm font-medium text-muted-foreground">Limites</h3>
              <TotaisPorCategoria totais={comLimite} soma={resumo.saidas} tipo="saida" vazio="" />
            </div>
          )}
        </Bloco>

        <Bloco
          titulo={mensal ? "Entradas e saídas por mês" : "Entradas e saídas por ciclo"}
          className="lg:col-span-2"
        >
          <GraficoEntradasSaidas
            periodos={historico}
            rotulo={`Gráfico de barras de entradas e saídas dos últimos ${historico.length} ${mensal ? "meses" : "ciclos"}`}
          />
        </Bloco>
        <div className="grid content-start gap-4">
          <Bloco titulo="De onde veio">
            <TotaisPorCategoria
              totais={resumo.entradas_por_categoria}
              soma={resumo.entradas}
              tipo="entrada"
              vazio={`Nenhuma entrada realizada neste ${nome}.`}
            />
          </Bloco>
          <Bloco
            titulo="Poupança"
            acao={
              <Button variant="link" size="sm" className="h-auto p-0" asChild>
                <Link href="/cartelas">Cartelas</Link>
              </Button>
            }
          >
            {cartelas.length === 0 ? (
              <p className="py-6 text-muted-foreground">
                Nenhuma cartela. O que sobrar do {nome} pode virar depósito numa meta.
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
      </div>

      <div className="order-2 mt-8 grid gap-4 md:mt-4 lg:grid-cols-2">
        <Bloco
          titulo="Últimos lançamentos do mês"
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
            vazio="Nenhum lançamento realizado neste mês."
            porPagina={POR_PAGINA}
          />
        </Bloco>
        <Bloco titulo={`Previstos do ${nome}`}>
          <ListaLancamentos
            lancamentos={previstos}
            categorias={categorias}
            sugestaoSalario={sugestaoSalario}
            vazio={`Nada previsto neste ${nome}.`}
            porPagina={POR_PAGINA}
          />
        </Bloco>
      </div>
    </section>
  )
}
