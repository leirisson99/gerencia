import type { Metadata } from "next"
import Link from "next/link"
import { notFound } from "next/navigation"
import { ArrowLeftIcon } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Bloco, Indicador } from "@/features/dashboard/bloco"
import { GerarCobranca } from "@/features/contas-compartilhadas/gerar-cobranca"
import { ListaParticipantes } from "@/features/contas-compartilhadas/lista-participantes"
import { VisaoParticipante } from "@/features/contas-compartilhadas/visao-participante"
import { MODOS, rotuloPendentes, rotuloPessoas } from "@/features/contas-compartilhadas/rotulos"
import { obterContaCompartilhada } from "@/lib/api/server"
import { formatarCentavos } from "@/lib/format"

export const metadata: Metadata = { title: "Conta compartilhada" }

/** Uma conta compartilhada: total do mês, quantas pessoas dividem e a parte de cada uma. */
export default async function ContaCompartilhadaPage({
  params,
}: PageProps<"/contas-compartilhadas/[id]">) {
  const { id } = await params
  if (!/^\d+$/.test(id)) notFound()

  const conta = await obterContaCompartilhada(Number(id))
  if (!conta) notFound()

  const pendentes = rotuloPendentes(conta.qtd_convidados_pendentes)

  return (
    <section aria-labelledby="conta-titulo">
      <Button variant="ghost" size="sm" className="-ml-2 mb-4" asChild>
        <Link href="/contas-compartilhadas">
          <ArrowLeftIcon aria-hidden />
          Contas compartilhadas
        </Link>
      </Button>

      <h1 id="conta-titulo" className="text-title">
        {conta.descricao}
      </h1>
      <p className="mt-2 text-muted-foreground">
        {conta.papel === "dono" ? `${MODOS[conta.modo]} · ` : ""}vence todo dia {conta.dia_vencimento}
        {!conta.ativa && " · desativada"}
      </p>

      {conta.papel === "participante" ? (
        <VisaoParticipante conta={conta} />
      ) : (
        <>
          <div className="mt-8 grid gap-4 sm:grid-cols-3">
            <Bloco titulo="Total do mês" acao={<GerarCobranca conta={conta} />}>
              <Indicador
                valor={conta.valor_total === null ? "—" : formatarCentavos(conta.valor_total)}
                legenda={
                  conta.valor_total !== null
                    ? undefined
                    : conta.falta_informar_total
                      ? "Falta informar o total deste mês."
                      : conta.valor_fixo !== null
                        ? `Valor fixo de ${formatarCentavos(conta.valor_fixo)}`
                        : undefined
                }
              />
            </Bloco>
            <Bloco titulo="Pessoas">
              <Indicador valor={rotuloPessoas(conta.qtd_pessoas)} legenda={pendentes ?? undefined} />
            </Bloco>
            <Bloco titulo="Sua parte">
              <Indicador
                valor={conta.minha_cota ? formatarCentavos(conta.minha_cota.valor) : "—"}
                legenda={conta.minha_cota ? undefined : "Aparece quando a cobrança do mês é gerada."}
              />
            </Bloco>
          </div>

          <ListaParticipantes conta={conta} />
        </>
      )}
    </section>
  )
}
