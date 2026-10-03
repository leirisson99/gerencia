import type { ReactNode } from "react"
import Link from "next/link"
import { CalendarDaysIcon } from "lucide-react"

import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar"
import { CarteiraProvider } from "@/features/carteira/contexto"
import { TipoRendaProvider } from "@/features/tipo-renda/contexto"
import type { Carteira, Categoria, Usuario } from "@/lib/api/types"
import { AppSidebar } from "./app-sidebar"
import { BarraInferior } from "./barra-inferior"
import { SeletorCarteira } from "./seletor-carteira"

type Props = {
  usuario: Usuario
  /** Estado salvo do menu (cookie `sidebar_state`), para não piscar ao carregar. */
  menuAberto: boolean
  /** Para o botão de lançar da barra inferior no celular. */
  categorias: Categoria[]
  sugestaoSalario: number | null
  /** Carteira aberta no seletor PF | PJ (cookie), já validada contra `usuario.tem_pj`. */
  carteira: Carteira
  children: ReactNode
}

/**
 * Moldura da área logada. No desktop: menu lateral à esquerda e conteúdo na largura toda.
 * No celular: saudação no topo e barra inferior de app. Cada página limita a própria largura.
 */
export function AppShell({ usuario, menuAberto, categorias, sugestaoSalario, carteira, children }: Props) {
  const primeiroNome = usuario.nome.trim().split(/\s+/)[0]
  return (
    <TipoRendaProvider tipo={usuario.tipo_renda}>
      <CarteiraProvider valor={{ carteira, temPj: usuario.tem_pj }}>
      <SidebarProvider defaultOpen={menuAberto}>
        <AppSidebar usuario={usuario} />
        <SidebarInset>
          <header className="flex h-16 items-center gap-3 px-4 pt-[env(safe-area-inset-top)] md:h-14 md:gap-2">
            <SidebarTrigger className="-ml-2 max-md:hidden" />
            <Link href="/perfil" className="flex min-w-0 items-center gap-3 md:hidden">
              <span
                aria-hidden
                className="flex size-10 shrink-0 items-center justify-center rounded-full bg-muted font-semibold uppercase"
              >
                {primeiroNome.charAt(0)}
              </span>
              <span className="min-w-0 leading-tight">
                <span className="block text-sm text-muted-foreground">Olá,</span>
                <span className="block truncate font-semibold">{primeiroNome}</span>
              </span>
            </Link>
            <div className="ml-auto flex items-center gap-2">
              <SeletorCarteira />
              <Link
                href="/calendario"
                aria-label="Calendário"
                className="flex size-10 items-center justify-center rounded-full bg-muted md:hidden"
              >
                <CalendarDaysIcon className="size-5" aria-hidden />
              </Link>
            </div>
          </header>
          <div className="w-full flex-1 px-4 pt-2 pb-[calc(6rem+env(safe-area-inset-bottom))] md:px-8 md:pt-4 md:pb-14">
            {children}
          </div>
        </SidebarInset>
        <BarraInferior categorias={categorias} sugestaoSalario={sugestaoSalario} />
      </SidebarProvider>
      </CarteiraProvider>
    </TipoRendaProvider>
  )
}
