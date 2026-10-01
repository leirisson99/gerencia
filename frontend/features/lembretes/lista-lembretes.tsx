import type { ReactNode } from "react"
import { cn } from "cn"

import { ListaLancamentos } from "@/features/lancamentos/lista-lancamentos"
import type { Categoria, ItemLembrete, LembreteLivre, LembretesOut } from "@/lib/api/types"
import { formatarData } from "@/lib/format"
import { ListaLivres } from "./lista-livres"

type Props = {
  lembretes: LembretesOut
  /** Todos os lembretes livres, inclusive concluídos e futuros. */
  livres: LembreteLivre[]
  categorias: Categoria[]
  sugestaoSalario: number | null
}

/**
 * Atrasados e a vencer até hoje + 3 dias, depois os próximos lembretes livres e os concluídos.
 * Contas e valores são lançamentos previstos: clicar abre a edição e "Paguei"/"Recebi" confirma
 * ali mesmo, como na lista de lançamentos.
 */
export function ListaLembretes({ lembretes, livres, categorias, sugestaoSalario }: Props) {
  const { atrasados, a_vencer: aVencer, limite } = lembretes
  const proximos = livres.filter((l) => !l.concluido && l.data > limite)
  const concluidos = livres.filter((l) => l.concluido)

  return (
    <div className="grid gap-10">
      {atrasados.length > 0 && (
        <Secao titulo="Atrasados" quantos={atrasados.length} destaque>
          <Itens itens={atrasados} categorias={categorias} sugestaoSalario={sugestaoSalario} />
        </Secao>
      )}

      <Secao titulo={`A vencer até ${formatarData(limite)}`} quantos={aVencer.length}>
        {aVencer.length === 0 ? (
          <p className="border-t py-8 text-muted-foreground">
            Nada vencendo de hoje até lá. Contas a pagar, valores a receber e lembretes aparecem
            aqui a partir de 3 dias antes da data.
          </p>
        ) : (
          <Itens itens={aVencer} categorias={categorias} sugestaoSalario={sugestaoSalario} />
        )}
      </Secao>

      {proximos.length > 0 && (
        <Secao titulo="Próximos lembretes" quantos={proximos.length}>
          <ListaLivres livres={proximos} />
        </Secao>
      )}

      {concluidos.length > 0 && (
        <details>
          <summary className="cursor-pointer text-sm text-muted-foreground select-none">
            {concluidos.length} {concluidos.length === 1 ? "lembrete concluído" : "lembretes concluídos"}
          </summary>
          <div className="mt-2">
            <ListaLivres livres={concluidos} />
          </div>
        </details>
      )}
    </div>
  )
}

/** Lançamentos primeiro (com "Paguei"/"Recebi"), depois os lembretes livres da mesma janela. */
function Itens({
  itens,
  categorias,
  sugestaoSalario,
}: {
  itens: ItemLembrete[]
  categorias: Categoria[]
  sugestaoSalario: number | null
}) {
  const lancamentos = itens.flatMap((i) => (i.lancamento ? [i.lancamento] : []))
  const livres = itens.flatMap((i) => (i.lembrete ? [i.lembrete] : []))
  return (
    <div className="grid gap-4">
      {lancamentos.length > 0 && (
        <ListaLancamentos
          lancamentos={lancamentos}
          categorias={categorias}
          sugestaoSalario={sugestaoSalario}
        />
      )}
      <ListaLivres livres={livres} />
    </div>
  )
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
