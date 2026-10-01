import type { Metadata } from "next"
import Link from "next/link"
import { redirect } from "next/navigation"

import { PageHeader } from "@/components/layout/page-header"
import { Barras } from "@/features/admin/barras"
import { GraficoCadastros, GraficoMovimentacoes } from "@/features/admin/graficos"
import { Bloco, Indicador } from "@/features/dashboard/bloco"
import { FORMAS } from "@/features/dividas/rotulos"
import { obterResumoAdmin } from "@/lib/api/server"
import type { Funcionalidade } from "@/lib/api/types"
import { TIPOS_RENDA } from "@/lib/tipo-renda"

export const metadata: Metadata = { title: "Visão geral" }

const FUNCIONALIDADES: Record<Funcionalidade, string> = {
  recorrencias: "Recorrências",
  dividas: "Dívidas",
  cartelas: "Cartelas de poupança",
  servicos: "Serviços a receber",
  importacao: "Importação de extrato",
}

const numero = new Intl.NumberFormat("pt-BR")

/** `parte` como porcentagem inteira de `todo`; zero quando não há contas. */
function porcento(parte: number, todo: number) {
  return todo ? `${Math.round((parte / todo) * 100)}%` : "0%"
}

/**
 * Visão geral da administração: só contagens somadas entre as contas, sem valores em reais nem
 * nada por conta (constituição 5.2.0, papel admin).
 */
export default async function AdminVisaoGeralPage({ searchParams }: PageProps<"/admin">) {
  // A lista de contas morava aqui; links antigos com busca ou filtro seguem para a página nova.
  const params = await searchParams
  if (params.busca || params.situacao) {
    const query = new URLSearchParams()
    for (const chave of ["busca", "situacao"] as const) {
      const valor = params[chave]
      if (typeof valor === "string") query.set(chave, valor)
    }
    redirect(`/admin/contas?${query}`)
  }

  const resumo = await obterResumoAdmin()
  const { contas, lancamentos, engajamento, dividas_por_forma: formas } = resumo
  const dividas = formas.reduce((soma, f) => soma + f.quantidade, 0)

  return (
    <>
      <PageHeader
        titulo="Visão geral"
        descricao="Uso do sistema somado entre todas as contas, sem valores em reais e sem nada por conta."
      />

      <div className="mb-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Bloco
          titulo="Contas"
          acao={
            <Link href="/admin/contas" className="text-sm text-muted-foreground underline-offset-4 hover:underline">
              Ver contas
            </Link>
          }
        >
          <Indicador
            valor={numero.format(contas.total)}
            legenda={`${numero.format(contas.ativas)} ativas · ${numero.format(contas.desativadas)} desativadas`}
          />
        </Bloco>
        <Bloco titulo="Acessaram em 30 dias">
          <Indicador
            valor={numero.format(engajamento.ativas_30_dias)}
            legenda={`${numero.format(engajamento.ativas_7_dias)} nos últimos 7 dias`}
          />
        </Bloco>
        <Bloco titulo="Ativação">
          <Indicador
            valor={porcento(engajamento.com_lancamento, contas.total)}
            legenda={`${numero.format(engajamento.com_lancamento)} de ${numero.format(contas.total)} contas já lançaram algo`}
          />
        </Bloco>
        <Bloco titulo="Lançamentos">
          <Indicador
            valor={numero.format(lancamentos.total)}
            legenda={
              <>
                {numero.format(lancamentos.realizados)} realizados · {numero.format(lancamentos.previstos)} previstos
                <br />
                {numero.format(lancamentos.importados)} importados · {numero.format(lancamentos.manuais)} manuais
              </>
            }
          />
        </Bloco>
      </div>

      <div className="mb-4 grid gap-4 lg:grid-cols-3">
        <Bloco titulo="Movimentações realizadas por mês" className="lg:col-span-2">
          <GraficoMovimentacoes meses={resumo.por_mes} />
        </Bloco>
        <Bloco titulo="Cadastros por mês">
          <GraficoCadastros meses={resumo.cadastros_por_mes} />
        </Bloco>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Bloco titulo="Contas que usam cada funcionalidade">
          <Barras
            base={contas.total}
            vazio="Nenhuma conta usa essas funcionalidades ainda."
            itens={resumo.uso_funcionalidades.map((u) => ({
              chave: u.funcionalidade,
              rotulo: FUNCIONALIDADES[u.funcionalidade],
              quantidade: u.contas,
            }))}
          />
        </Bloco>
        <Bloco titulo="Contas por tipo de renda">
          <Barras
            base={contas.total}
            vazio="Nenhuma conta cadastrada ainda."
            itens={TIPOS_RENDA.map((t) => ({
              chave: t.valor,
              rotulo: t.rotulo,
              quantidade: resumo.por_tipo_renda[t.valor],
            }))}
          />
        </Bloco>
        <Bloco titulo="Formas de pagamento das dívidas">
          <Barras
            base={dividas}
            vazio="Nenhuma dívida cadastrada ainda."
            itens={formas.map((f) => ({ chave: f.forma, rotulo: FORMAS[f.forma], quantidade: f.quantidade }))}
          />
        </Bloco>
      </div>
    </>
  )
}
