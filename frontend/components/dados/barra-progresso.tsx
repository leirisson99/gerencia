import { cn } from "cn"

type Props = {
  /** Quanto já foi (centavos ou unidades, na mesma escala de `total`). */
  valor: number
  total: number
  className?: string
}

/** Progresso de valor sobre total. O trilho é um tom mais claro da mesma cor (medidor, não gráfico). */
export function BarraProgresso({ valor, total, className }: Props) {
  // Proporção só para desenhar; os valores vêm prontos da API.
  const largura = total > 0 ? Math.min((valor / total) * 100, 100) : 0
  return (
    <div className={cn("h-2 rounded-full bg-foreground/10", className)} aria-hidden>
      <div className="h-full rounded-full bg-foreground" style={{ width: `${largura}%` }} />
    </div>
  )
}
