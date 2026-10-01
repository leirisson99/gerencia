import Link from "next/link"
import { cn } from "cn"
import {
  ArrowDownIcon,
  ArrowUpIcon,
  HandCoinsIcon,
  RepeatIcon,
  TagsIcon,
  UploadIcon,
  type LucideIcon,
} from "lucide-react"

import { formatarCentavos } from "@/lib/format"

/**
 * Cartão do topo do dashboard no celular: saldo do ciclo (ou do mês) em destaque, com entradas e saídas logo
 * abaixo. Fundo invertido (preto no tema claro, branco no escuro) para ser o primeiro olhar.
 */
export function SaldoDestaque({
  saldo,
  entradas,
  saidas,
  periodo,
  diaDoCiclo,
  nome = "ciclo",
}: {
  saldo: number
  entradas: number
  saidas: number
  periodo: string
  diaDoCiclo: number
  /** "mês" para o prestador. */
  nome?: "ciclo" | "mês"
}) {
  return (
    <section
      aria-label={`Saldo do ${nome}`}
      className="rounded-3xl bg-primary p-5 text-primary-foreground shadow-sm"
    >
      <p className="text-center text-sm opacity-70">Saldo do {nome}</p>
      <p
        className={cn(
          "valor mt-1 text-center text-[2.5rem] leading-none font-semibold tracking-tight",
          saldo < 0 && "text-saida"
        )}
      >
        {formatarCentavos(saldo)}
      </p>
      <p className="valor mt-2 text-center text-xs opacity-70">
        {periodo} · {diaDoCiclo}º dia
      </p>

      <div className="mt-5 grid grid-cols-2 gap-3">
        <Movimento titulo="Entradas" valor={entradas} icone={ArrowDownIcon} />
        <Movimento titulo="Saídas" valor={saidas} icone={ArrowUpIcon} saida />
      </div>
    </section>
  )
}

function Movimento({
  titulo,
  valor,
  icone: Icone,
  saida = false,
}: {
  titulo: string
  valor: number
  icone: LucideIcon
  saida?: boolean
}) {
  return (
    <div className="relative overflow-hidden rounded-2xl bg-primary-foreground/10 p-3">
      <Icone
        aria-hidden
        className="absolute -right-3 -bottom-3 size-16 opacity-10"
        strokeWidth={2.5}
      />
      <span
        aria-hidden
        className="flex size-7 items-center justify-center rounded-full bg-primary-foreground text-primary"
      >
        <Icone className="size-4" />
      </span>
      <p className="mt-3 text-xs opacity-70">{titulo}</p>
      <p className={cn("valor font-semibold", saida && "text-saida")}>
        {formatarCentavos(valor)}
      </p>
    </div>
  )
}

const ATALHOS: { titulo: string; href: string; icone: LucideIcon }[] = [
  { titulo: "Importar", href: "/importar", icone: UploadIcon },
  { titulo: "Fixos", href: "/recorrencias", icone: RepeatIcon },
  { titulo: "Dívidas", href: "/dividas", icone: HandCoinsIcon },
  { titulo: "Categorias", href: "/categorias", icone: TagsIcon },
]

/** Atalhos redondos para as páginas mais usadas depois do dashboard, no celular. */
export function Atalhos({ className }: { className?: string }) {
  return (
    <nav aria-label="Atalhos" className={className}>
      <ul className="grid grid-cols-4 gap-2">
        {ATALHOS.map(({ titulo, href, icone: Icone }) => (
          <li key={href}>
            <Link
              href={href}
              className="flex flex-col items-center gap-2 text-xs active:opacity-70"
            >
              <span className="flex size-14 items-center justify-center rounded-full border bg-card">
                <Icone className="size-5" aria-hidden />
              </span>
              {titulo}
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  )
}
