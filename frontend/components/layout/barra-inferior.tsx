"use client"

import { useState } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "cn"
import {
  ArrowUpIcon,
  HouseIcon,
  ListIcon,
  MenuIcon,
  PiggyBankIcon,
  PlusIcon,
  type LucideIcon,
} from "lucide-react"

import { useSidebar } from "@/components/ui/sidebar"
import { DialogLancamento } from "@/features/lancamentos/dialog-lancamento"
import { useTipoRenda } from "@/features/tipo-renda/contexto"
import type { Categoria } from "@/lib/api/types"
import { ehPrestador } from "@/lib/tipo-renda"

type Props = {
  categorias: Categoria[]
  sugestaoSalario: number | null
}

function ativo(href: string, pathname: string) {
  return href === "/" ? pathname === "/" : pathname === href || pathname.startsWith(`${href}/`)
}

/**
 * Navegação de app no celular: quatro destinos e o botão central de lançar uma saída, que é a ação
 * mais frequente. "Mais" abre o menu lateral com o resto das páginas. Some a partir de md.
 */
export function BarraInferior({ categorias, sugestaoSalario }: Props) {
  const pathname = usePathname()
  const { setOpenMobile } = useSidebar()
  const [lancando, setLancando] = useState(false)
  // Sem nenhum salário ainda não há ciclo e a API recusa saídas: o botão abre o lançamento
  // completo para o salário aparecer. A sugestão só é nula quando nunca houve salário.
  const semCiclo = !ehPrestador(useTipoRenda()) && sugestaoSalario === null
  const Icone = semCiclo ? PlusIcon : ArrowUpIcon

  return (
    <>
      <nav
        aria-label="Navegação principal"
        className="fixed inset-x-0 bottom-0 z-40 border-t bg-background/95 pb-[env(safe-area-inset-bottom)] backdrop-blur supports-backdrop-filter:bg-background/80 md:hidden"
      >
        <ul className="mx-auto grid h-16 max-w-md grid-cols-5 items-center px-2">
          <ItemBarra href="/" titulo="Início" icone={HouseIcon} ativo={ativo("/", pathname)} />
          <ItemBarra
            href="/lancamentos"
            titulo="Lançamentos"
            icone={ListIcon}
            ativo={ativo("/lancamentos", pathname)}
          />
          <li className="flex justify-center">
            <button
              type="button"
              onClick={() => setLancando(true)}
              aria-label={semCiclo ? "Novo lançamento" : "Nova saída"}
              className="-mt-8 flex size-14 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-lg ring-4 ring-background transition-transform active:scale-95 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
            >
              <Icone className="size-6" aria-hidden />
            </button>
          </li>
          <ItemBarra
            href="/cartelas"
            titulo="Cartelas"
            icone={PiggyBankIcon}
            ativo={ativo("/cartelas", pathname)}
          />
          <li>
            <button
              type="button"
              onClick={() => setOpenMobile(true)}
              className="flex w-full flex-col items-center gap-1 py-1 text-[0.6875rem] text-muted-foreground"
            >
              <MenuIcon className="size-5" aria-hidden />
              Mais
            </button>
          </li>
        </ul>
      </nav>

      <DialogLancamento
        aberto={lancando}
        aoMudar={setLancando}
        categorias={categorias}
        sugestaoSalario={sugestaoSalario}
        tipo={semCiclo ? undefined : "saida"}
      />
    </>
  )
}

function ItemBarra({
  href,
  titulo,
  icone: Icone,
  ativo,
}: {
  href: string
  titulo: string
  icone: LucideIcon
  ativo: boolean
}) {
  return (
    <li>
      <Link
        href={href}
        aria-current={ativo ? "page" : undefined}
        className={cn(
          "flex flex-col items-center gap-1 py-1 text-[0.6875rem]",
          ativo ? "font-medium text-foreground" : "text-muted-foreground"
        )}
      >
        <Icone className="size-5" strokeWidth={ativo ? 2.25 : 1.75} aria-hidden />
        {titulo}
      </Link>
    </li>
  )
}
