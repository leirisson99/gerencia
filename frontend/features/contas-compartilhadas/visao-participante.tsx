import { Bloco, Indicador } from "@/features/dashboard/bloco"
import type { ContaParticipante } from "@/lib/api/types"
import { formatarCentavos } from "@/lib/format"
import { SairDaConta } from "./sair-da-conta"
import { rotuloPendentes, rotuloPessoas, STATUS_COTA } from "./rotulos"

/** O que um participante vê: total, pessoas, a própria parte e, dos demais, só nome e status. */
export function VisaoParticipante({ conta }: { conta: ContaParticipante }) {
  const pendentes = rotuloPendentes(conta.qtd_convidados_pendentes)
  return (
    <>
      <div className="mt-8 grid gap-4 sm:grid-cols-3">
        <Bloco titulo="Total do mês">
          <Indicador
            valor={conta.valor_total === null ? "—" : formatarCentavos(conta.valor_total)}
            legenda={conta.valor_total === null ? "O dono ainda não informou o total." : undefined}
          />
        </Bloco>
        <Bloco titulo="Pessoas">
          <Indicador valor={rotuloPessoas(conta.qtd_pessoas)} legenda={pendentes ?? undefined} />
        </Bloco>
        <Bloco titulo="Sua parte">
          <Indicador
            valor={conta.minha_cota ? formatarCentavos(conta.minha_cota.valor) : "—"}
            legenda={
              conta.minha_cota
                ? STATUS_COTA[conta.minha_cota.status]
                : "Aparece quando a cobrança do mês é gerada."
            }
          />
        </Bloco>
      </div>

      <section aria-labelledby="participantes-titulo" className="mt-12">
        <h2 id="participantes-titulo" className="mb-3 text-sm font-medium text-muted-foreground">
          Quem divide
        </h2>
        <ul className="divide-y rounded-lg border">
          <li className="flex items-center justify-between gap-3 p-4">
            <p className="font-medium">Você</p>
            <span className="text-sm text-muted-foreground">
              {conta.minha_cota ? STATUS_COTA[conta.minha_cota.status] : "Aceitou"}
            </span>
          </li>
          {conta.outros.map((o, i) => (
            <li key={`${o.nome}-${i}`} className="flex items-center justify-between gap-3 p-4">
              <p className="min-w-0 truncate font-medium">{o.nome}</p>
              <span className="shrink-0 text-sm text-muted-foreground">{STATUS_COTA[o.status]}</span>
            </li>
          ))}
        </ul>
        <div className="mt-6">
          <SairDaConta contaId={conta.id} descricao={conta.descricao} />
        </div>
      </section>
    </>
  )
}
