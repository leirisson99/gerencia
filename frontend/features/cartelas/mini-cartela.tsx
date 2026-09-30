import { cn } from "cn"

import { BarraProgresso } from "@/components/dados/barra-progresso"
import type { Cartela } from "@/lib/api/types"

// Acima disso os quadradinhos ficam pequenos demais; a barra comunica melhor.
const MAX_CASAS = 120

/**
 * A cartela em miniatura: um quadradinho por casa, preenchido quando depositada, vazio quando
 * livre e tracejado na casa de ajuste. Decorativa: o texto ao lado já traz os números.
 */
export function MiniCartela({ cartela, className }: { cartela: Cartela; className?: string }) {
  if (cartela.casas.length > MAX_CASAS) {
    return <BarraProgresso valor={cartela.guardado} total={cartela.meta} className={className} />
  }
  return (
    <div className={cn("flex flex-wrap gap-[3px]", className)} aria-hidden>
      {cartela.casas.map((casa) => (
        <span
          key={casa.id}
          className={cn(
            "size-2.5 rounded-[2px]",
            casa.depositado_em
              ? "bg-foreground"
              : casa.is_ajuste
                ? "border border-dashed border-foreground/50"
                : "bg-foreground/12"
          )}
        />
      ))}
    </div>
  )
}
