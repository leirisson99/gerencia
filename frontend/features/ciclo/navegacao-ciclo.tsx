import type { ReactNode } from "react"
import Link from "next/link"
import { ChevronLeftIcon, ChevronRightIcon } from "lucide-react"

import { Button } from "@/components/ui/button"
import type { Ciclo } from "@/lib/api/types"
import { formatarData, formatarMes } from "@/lib/format"

type PropsNavegacao = {
  ciclo: Ciclo
  /** Prestador: o ciclo é o mês do calendário e os textos falam em mês. */
  mensal?: boolean
}

/** Período do ciclo e links para os vizinhos. Sem vizinho, o botão fica desabilitado. */
export function NavegacaoCiclo({ ciclo, mensal = false }: PropsNavegacao) {
  const r = rotulos(mensal)
  return (
    <nav aria-label={r.grupo} className="flex items-center gap-1">
      <BotaoVizinho
        href={ciclo.anterior && `/lancamentos?ciclo=${ciclo.anterior}`}
        rotulo={r.anterior}
        icone={<ChevronLeftIcon aria-hidden />}
      />
      <BotaoVizinho
        href={ciclo.proximo && `/lancamentos?ciclo=${ciclo.proximo}`}
        rotulo={r.proximo}
        icone={<ChevronRightIcon aria-hidden />}
      />
    </nav>
  )
}

/**
 * Versão de celular: uma pílula com o ciclo no meio e as setas nas pontas, na largura toda.
 * O título da página fica aqui dentro, no lugar do cabeçalho grande.
 */
export function NavegacaoCicloCompacta({
  ciclo,
  mensal = false,
  tituloId,
}: PropsNavegacao & { tituloId?: string }) {
  const r = rotulos(mensal)
  return (
    <nav aria-label={r.grupo} className="flex items-center gap-2 rounded-full border p-1">
      <BotaoVizinho
        href={ciclo.anterior && `/lancamentos?ciclo=${ciclo.anterior}`}
        rotulo={r.anterior}
        icone={<ChevronLeftIcon aria-hidden />}
        compacto
      />
      <div className="min-w-0 flex-1 text-center leading-tight">
        <h1 id={tituloId} className="truncate text-sm font-semibold">
          {tituloCiclo(ciclo, mensal)}
        </h1>
        <p className="valor truncate text-xs text-muted-foreground">{periodoCiclo(ciclo, mensal)}</p>
      </div>
      <BotaoVizinho
        href={ciclo.proximo && `/lancamentos?ciclo=${ciclo.proximo}`}
        rotulo={r.proximo}
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

function rotulos(mensal: boolean) {
  return mensal
    ? { grupo: "Meses", anterior: "Mês anterior", proximo: "Próximo mês" }
    : { grupo: "Ciclos", anterior: "Ciclo anterior", proximo: "Próximo ciclo" }
}

/** `Ciclo atual` / `Ciclo encerrado`, ou `Mês atual` / `Mês encerrado` para o prestador. */
export function tituloCiclo(ciclo: Ciclo, mensal = false): string {
  return `${mensal ? "Mês" : "Ciclo"} ${ciclo.aberto ? "atual" : "encerrado"}`
}

/**
 * `Desde 05/10/2026` no aberto; `05/10/2026 a 05/11/2026` nos fechados. Para o prestador, o nome
 * do mês: `outubro de 2026`.
 */
export function periodoCiclo(ciclo: Ciclo, mensal = false): string {
  if (mensal) return formatarMes(ciclo.inicio.slice(0, 7))
  return ciclo.fim
    ? `${formatarData(ciclo.inicio)} a ${formatarData(ciclo.fim)}`
    : `Desde ${formatarData(ciclo.inicio)}`
}
