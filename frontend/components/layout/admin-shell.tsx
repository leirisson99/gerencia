import type { ReactNode } from "react"

import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar"
import type { Usuario } from "@/lib/api/types"
import { AdminSidebar } from "./admin-sidebar"

/**
 * Moldura da administração: menu lateral (gaveta no celular) e conteúdo na largura toda.
 * Sem nada financeiro: só a visão geral, as contas e a própria conta.
 */
export function AdminShell({
  usuario,
  menuAberto,
  children,
}: {
  usuario: Pick<Usuario, "nome" | "email">
  /** Estado salvo do menu (cookie `sidebar_state`), para não piscar ao carregar. */
  menuAberto: boolean
  children: ReactNode
}) {
  return (
    <SidebarProvider defaultOpen={menuAberto}>
      <AdminSidebar usuario={usuario} />
      <SidebarInset>
        <header className="flex h-14 items-center gap-2 px-4 pt-[env(safe-area-inset-top)]">
          <SidebarTrigger className="-ml-2" />
          <span className="text-sm text-muted-foreground md:hidden">Administração</span>
        </header>
        <div className="w-full flex-1 px-4 pt-2 pb-14 md:px-8 md:pt-4">{children}</div>
      </SidebarInset>
    </SidebarProvider>
  )
}
