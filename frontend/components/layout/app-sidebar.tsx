"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import {
  BellIcon,
  CalendarDaysIcon,
  BriefcaseIcon,
  ChevronsUpDownIcon,
  HandCoinsIcon,
  LayoutDashboardIcon,
  ListIcon,
  LogOutIcon,
  PiggyBankIcon,
  RepeatIcon,
  TagsIcon,
  UploadIcon,
  UserIcon,
  type LucideIcon,
} from "lucide-react"

import { Logo, Marca } from "@/components/brand/logo"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
  useSidebar,
} from "@/components/ui/sidebar"
import { useSair } from "@/features/auth/use-sair"
import { useTipoRenda } from "@/features/tipo-renda/contexto"
import type { TipoRenda, Usuario } from "@/lib/api/types"
import { temServicos } from "@/lib/tipo-renda"

type Item = {
  titulo: string
  href: string
  icone: LucideIcon
  /** Só aparece para esses tipos de renda. */
  visivel?: (tipo: TipoRenda) => boolean
}
type Grupo = { titulo: string; itens: Item[] }

// Só páginas que já existem; novas entradas chegam junto com suas features.
const GRUPOS: Grupo[] = [
  {
    titulo: "Visão",
    itens: [
      { titulo: "Dashboard", href: "/", icone: LayoutDashboardIcon },
      { titulo: "Lançamentos", href: "/lancamentos", icone: ListIcon },
      { titulo: "Lembretes", href: "/lembretes", icone: BellIcon },
      { titulo: "Importar extrato", href: "/importar", icone: UploadIcon },
      { titulo: "Calendário", href: "/calendario", icone: CalendarDaysIcon },
    ],
  },
  {
    titulo: "Cadastros",
    itens: [
      { titulo: "Categorias", href: "/categorias", icone: TagsIcon },
      { titulo: "Recorrências", href: "/recorrencias", icone: RepeatIcon },
      { titulo: "Serviços", href: "/servicos", icone: BriefcaseIcon, visivel: temServicos },
      { titulo: "Dívidas", href: "/dividas", icone: HandCoinsIcon },
      { titulo: "Cartelas", href: "/cartelas", icone: PiggyBankIcon },
    ],
  },
  {
    titulo: "Conta",
    itens: [{ titulo: "Perfil", href: "/perfil", icone: UserIcon }],
  },
]

function itemAtivo(href: string, pathname: string) {
  return href === "/" ? pathname === "/" : pathname === href || pathname.startsWith(`${href}/`)
}

/** Menu lateral da área logada. No celular vira uma gaveta; no desktop recolhe para ícones. */
export function AppSidebar({ usuario }: { usuario: Pick<Usuario, "nome" | "email"> }) {
  const pathname = usePathname()
  const { isMobile, setOpenMobile } = useSidebar()
  const tipoRenda = useTipoRenda()

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader className="h-14 justify-center px-4 group-data-[collapsible=icon]:px-2">
        <Logo className="text-lg group-data-[collapsible=icon]:hidden" />
        <Link
          href="/"
          aria-label="Dashboard"
          className="hidden size-8 items-center justify-center group-data-[collapsible=icon]:flex"
        >
          <Marca className="size-7" />
        </Link>
      </SidebarHeader>

      <SidebarContent>
        {GRUPOS.map((grupo) => (
          <SidebarGroup key={grupo.titulo}>
            <SidebarGroupLabel>{grupo.titulo}</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {grupo.itens.filter((item) => item.visivel?.(tipoRenda) ?? true).map((item) => {
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
        ))}
      </SidebarContent>

      <SidebarFooter>
        <MenuUsuario usuario={usuario} />
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  )
}

function MenuUsuario({ usuario }: { usuario: Pick<Usuario, "nome" | "email"> }) {
  const { isMobile } = useSidebar()
  const aoSair = useSair()

  return (
    <SidebarMenu>
      <SidebarMenuItem>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <SidebarMenuButton size="lg" tooltip={usuario.nome}>
              <span
                aria-hidden
                className="flex size-8 shrink-0 items-center justify-center rounded-md bg-sidebar-accent font-medium uppercase"
              >
                {usuario.nome.trim().charAt(0)}
              </span>
              <span className="grid min-w-0 flex-1 text-left leading-tight">
                <span className="truncate font-medium">{usuario.nome}</span>
                <span className="truncate text-xs text-muted-foreground">{usuario.email}</span>
              </span>
              <ChevronsUpDownIcon className="ml-auto text-muted-foreground" aria-hidden />
            </SidebarMenuButton>
          </DropdownMenuTrigger>
          <DropdownMenuContent
            side={isMobile ? "top" : "right"}
            align="end"
            className="w-56"
          >
            <DropdownMenuLabel className="truncate font-normal text-muted-foreground">
              {usuario.email}
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem asChild>
              <Link href="/perfil">
                <UserIcon aria-hidden />
                Perfil
              </Link>
            </DropdownMenuItem>
            <DropdownMenuItem onSelect={aoSair}>
              <LogOutIcon aria-hidden />
              Sair
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </SidebarMenuItem>
    </SidebarMenu>
  )
}
