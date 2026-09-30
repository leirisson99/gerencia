import type { ReactNode } from "react"
import { cn } from "cn"

/** Área do dashboard com título pequeno e ação opcional à direita. */
export function Bloco({
  titulo,
  acao,
  className,
  children,
}: {
  titulo: string
  acao?: ReactNode
  className?: string
  children: ReactNode
}) {
  return (
    <section className={cn("rounded-2xl border p-4 md:rounded-lg md:p-5", className)}>
      <div className="mb-3 flex items-center justify-between gap-2">
        {/* No celular o título pesa mais, como seção de app; no desktop fica discreto. */}
        <h2 className="font-semibold md:text-sm md:font-medium md:text-muted-foreground">{titulo}</h2>
        {acao}
      </div>
      {children}
    </section>
  )
}

/** Número de destaque com legenda, para os blocos do topo. */
export function Indicador({
  valor,
  legenda,
  className,
}: {
  valor: ReactNode
  legenda?: ReactNode
  /** Ex.: tamanho maior para o número principal ou cor de saída. */
  className?: string
}) {
  return (
    <>
      <p className={cn("valor text-title", className)}>{valor}</p>
      {legenda && <p className="mt-1 text-sm text-muted-foreground">{legenda}</p>}
    </>
  )
}
