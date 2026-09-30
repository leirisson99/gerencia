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

/**
 * Versão de celular: uma pílula com o ciclo no meio e as setas nas pontas, na largura toda.
 * O título da página fica aqui dentro, no lugar do cabeçalho grande.
 */
export function NavegacaoCicloCompacta({ ciclo, tituloId }: { ciclo: Ciclo; tituloId?: string }) {
  return (
    <nav aria-label="Ciclos" className="flex items-center gap-2 rounded-full border p-1">
      <BotaoVizinho
        href={ciclo.anterior && `/lancamentos?ciclo=${ciclo.anterior}`}
        rotulo="Ciclo anterior"
        icone={<ChevronLeftIcon aria-hidden />}
        compacto
      />
      <div className="min-w-0 flex-1 text-center leading-tight">
        <h1 id={tituloId} className="truncate text-sm font-semibold">
          {ciclo.aberto ? "Ciclo atual" : "Ciclo encerrado"}
        </h1>
        <p className="valor truncate text-xs text-muted-foreground">{periodoCiclo(ciclo)}</p>
      </div>
      <BotaoVizinho
        href={ciclo.proximo && `/lancamentos?ciclo=${ciclo.proximo}`}
        rotulo="Próximo ciclo"
        icone={<ChevronRightIcon aria-hidden />}
        compacto
      />
    </nav>
  )
}

function BotaoVizinho({
  href,
  rotulo,
  icone,
  compacto = false,
}: {
  href: string | null
  rotulo: string
  icone: ReactNode
  /** Redondo e sem borda, para ficar dentro da pílula do celular. */
  compacto?: boolean
}) {
  const variant = compacto ? "ghost" : "outline"
  const className = compacto ? "rounded-full" : undefined
  if (!href) {
    return (
      <Button variant={variant} size="icon" className={className} disabled aria-label={`${rotulo}: não existe`}>
        {icone}
      </Button>
    )
  }
  return (
    <Button variant={variant} size="icon" className={className} asChild>
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
