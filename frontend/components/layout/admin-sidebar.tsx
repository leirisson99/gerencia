"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { LayoutDashboardIcon, UsersIcon } from "lucide-react"

import { Logo, Marca } from "@/components/brand/logo"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
  useSidebar,
} from "@/components/ui/sidebar"
import type { Usuario } from "@/lib/api/types"
import { MenuUsuario } from "./app-sidebar"

const ITENS = [
  { titulo: "Visão geral", href: "/admin", icone: LayoutDashboardIcon },
  { titulo: "Contas", href: "/admin/contas", icone: UsersIcon },
]

function itemAtivo(href: string, pathname: string) {
  return href === "/admin" ? pathname === "/admin" : pathname.startsWith(href)
}

/** Menu lateral da administração, no mesmo molde do menu da área logada. */
export function AdminSidebar({ usuario }: { usuario: Pick<Usuario, "nome" | "email"> }) {
  const pathname = usePathname()
  const { isMobile, setOpenMobile } = useSidebar()

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader className="h-14 justify-center px-4 group-data-[collapsible=icon]:px-2">
        <div className="flex items-baseline gap-2 group-data-[collapsible=icon]:hidden">
          <Logo className="text-lg" href="/admin" />
          <span className="text-xs text-muted-foreground">Admin</span>
        </div>
        <Link
          href="/admin"
          aria-label="Visão geral"
          className="hidden size-8 items-center justify-center group-data-[collapsible=icon]:flex"
        >
          <Marca className="size-7" />
        </Link>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              {ITENS.map((item) => {
                const ativo = itemAtivo(item.href, pathname)
                return (
                  <SidebarMenuItem key={item.href}>
                    <SidebarMenuButton asChild isActive={ativo} tooltip={item.titulo}>
                      <Link
                        href={item.href}
                        aria-current={ativo ? "page" : undefined}
                        onClick={() => isMobile && setOpenMobile(false)}
                      >
                        <item.icone aria-hidden />
                        <span>{item.titulo}</span>
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                )
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter>
        <MenuUsuario usuario={usuario} conta={{ titulo: "Minha conta", href: "/admin/conta" }} />
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  )
}
