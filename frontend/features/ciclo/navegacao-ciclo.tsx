import type { ReactNode } from "react"
import Link from "next/link"
import { ChevronLeftIcon, ChevronRightIcon } from "lucide-react"

import { Button } from "@/components/ui/button"
import type { Ciclo } from "@/lib/api/types"
import { formatarData } from "@/lib/format"

/** Período do ciclo e links para os vizinhos. Sem vizinho, o botão fica desabilitado. */
export function NavegacaoCiclo({ ciclo }: { ciclo: Ciclo }) {
  return (
    <nav aria-label="Ciclos" className="flex items-center gap-1">
      <BotaoVizinho
        href={ciclo.anterior && `/lancamentos?ciclo=${ciclo.anterior}`}
        rotulo="Ciclo anterior"
        icone={<ChevronLeftIcon aria-hidden />}
      />
      <BotaoVizinho
        href={ciclo.proximo && `/lancamentos?ciclo=${ciclo.proximo}`}
        rotulo="Próximo ciclo"
        icone={<ChevronRightIcon aria-hidden />}
      />
    </nav>
  )
}

function BotaoVizinho({ href, rotulo, icone }: { href: string | null; rotulo: string; icone: ReactNode }) {
  if (!href) {
    return (
      <Button variant="outline" size="icon" disabled aria-label={`${rotulo}: não existe`}>
        {icone}
      </Button>
    )
  }
  return (
    <Button variant="outline" size="icon" asChild>
      <Link href={href} aria-label={rotulo} title={rotulo}>
        {icone}
      </Link>
    </Button>
  )
}

/** `Desde 05/10/2026` no aberto; `05/10/2026 a 05/11/2026` nos fechados. */
export function periodoCiclo(ciclo: Ciclo): string {
  return ciclo.fim
    ? `${formatarData(ciclo.inicio)} a ${formatarData(ciclo.fim)}`
    : `Desde ${formatarData(ciclo.inicio)}`
}
