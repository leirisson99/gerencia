import type { ReactNode } from "react"
import { cn } from "cn"

import { ListaLancamentos } from "@/features/lancamentos/lista-lancamentos"
import type { Categoria, ItemLembrete, LembretesOut } from "@/lib/api/types"
import { formatarData } from "@/lib/format"

type Props = {
  lembretes: LembretesOut
  categorias: Categoria[]
  sugestaoSalario: number | null
}

/**
 * Atrasados e a vencer até hoje + 3 dias. Os itens são lançamentos previstos: clicar abre a
 * edição e "Paguei"/"Recebi" confirma ali mesmo, como na lista de lançamentos.
 */
export function ListaLembretes({ lembretes, categorias, sugestaoSalario }: Props) {
  const { atrasados, a_vencer: aVencer, limite } = lembretes

  if (atrasados.length === 0 && aVencer.length === 0) {
    return (
      <p className="border-t py-8 text-muted-foreground">
        Nada vencendo nos próximos 3 dias. Contas a pagar e valores a receber previstos aparecem
        aqui a partir de 3 dias antes da data.
      </p>
    )
  }

  return (
    <div className="grid gap-10">
      {atrasados.length > 0 && (
        <Secao titulo="Atrasados" quantos={atrasados.length} destaque>
          <ListaLancamentos
            lancamentos={lancamentosDe(atrasados)}
            categorias={categorias}
            sugestaoSalario={sugestaoSalario}
          />
        </Secao>
      )}
      <Secao titulo={`A vencer até ${formatarData(limite)}`} quantos={aVencer.length}>
        <ListaLancamentos
          lancamentos={lancamentosDe(aVencer)}
          categorias={categorias}
          sugestaoSalario={sugestaoSalario}
          vazio="Nada vencendo de hoje até lá."
        />
      </Secao>
    </div>
  )
}

function lancamentosDe(itens: ItemLembrete[]) {
  return itens.flatMap((item) => (item.lancamento ? [item.lancamento] : []))
}

function Secao({
  titulo,
  quantos,
  destaque = false,
  children,
}: {
  titulo: string
  quantos: number
  /** Atrasados em vermelho, para ser o primeiro olhar. */
  destaque?: boolean
  children: ReactNode
}) {
  return (
    <section aria-label={titulo}>
      <h2
        className={cn(
          "mb-3 flex items-baseline gap-2 font-semibold md:text-sm md:font-medium",
          destaque ? "text-saida" : "md:text-muted-foreground"
        )}
      >
        {titulo}
        <span className="valor text-xs font-normal opacity-70">{quantos}</span>
      </h2>
      {children}
    </section>
  )
}
