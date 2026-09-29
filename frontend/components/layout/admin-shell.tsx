"use client"

import type { ReactNode } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "cn"
import { LogOutIcon } from "lucide-react"

import { Logo } from "@/components/brand/logo"
import { Button } from "@/components/ui/button"
import { useSair } from "@/features/auth/use-sair"
import type { Usuario } from "@/lib/api/types"

const LINKS = [
  { titulo: "Contas", href: "/admin" },
  { titulo: "Minha conta", href: "/admin/conta" },
]

/** Moldura da área do administrador: sem menu financeiro, só o painel, a própria conta e sair. */
export function AdminShell({ usuario, children }: { usuario: Pick<Usuario, "email">; children: ReactNode }) {
  const pathname = usePathname()
  const aoSair = useSair()

  return (
    <div className="flex min-h-dvh flex-col">
      <header className="border-b">
        <div className="flex h-14 items-center justify-between gap-4 px-4 md:px-8">
          <div className="flex items-baseline gap-3">
            <Logo className="text-lg" href="/admin" />
            <span className="text-sm text-muted-foreground">Administração</span>
          </div>
          <div className="flex min-w-0 items-center gap-2">
            <Link
              href="/admin/conta"
              className="hidden truncate text-sm text-muted-foreground hover:text-foreground sm:inline"
            >
              {usuario.email}
            </Link>
            <Button variant="ghost" size="sm" onClick={aoSair}>
              <LogOutIcon aria-hidden />
              Sair
            </Button>
          </div>
        </div>
        <nav aria-label="Administração" className="flex gap-1 px-2 md:px-6">
          {LINKS.map((link) => {
            const ativo = pathname === link.href
            return (
              <Link
                key={link.href}
                href={link.href}
                aria-current={ativo ? "page" : undefined}
                className={cn(
                  "-mb-px border-b-2 px-2 py-2.5 text-sm transition-colors",
                  ativo
                    ? "border-foreground font-medium text-foreground"
                    : "border-transparent text-muted-foreground hover:text-foreground"
                )}
              >
                {link.titulo}
              </Link>
            )
          })}
        </nav>
      </header>
      <main className="w-full flex-1 px-4 py-8 md:px-8">{children}</main>
    </div>
  )
}
