import type { ReactNode } from "react"

import { Logo } from "@/components/brand/logo"
import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar"
import type { Usuario } from "@/lib/api/types"
import { AppSidebar } from "./app-sidebar"

type Props = {
  usuario: Usuario
  /** Estado salvo do menu (cookie `sidebar_state`), para não piscar ao carregar. */
  menuAberto: boolean
  children: ReactNode
}

/** Moldura da área logada: menu lateral à esquerda e conteúdo na largura toda. Cada página limita a própria largura. */
export function AppShell({ usuario, menuAberto, children }: Props) {
  return (
    <SidebarProvider defaultOpen={menuAberto}>
      <AppSidebar usuario={usuario} />
      <SidebarInset>
        <header className="flex h-14 items-center gap-2 border-b px-4 md:border-b-0">
          <SidebarTrigger className="-ml-2" />
          <Logo className="text-lg md:hidden" />
        </header>
        <div className="w-full flex-1 px-4 pt-6 pb-10 sm:pb-14 md:px-8 md:pt-4">
          {children}
        </div>
      </SidebarInset>
    </SidebarProvider>
  )
}
