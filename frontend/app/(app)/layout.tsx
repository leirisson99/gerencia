import { cookies } from "next/headers"
import { redirect } from "next/navigation"

import { AppShell } from "@/components/layout/app-shell"
import { listarCategorias, obterSugestaoSalario, obterUsuarioSessao } from "@/lib/api/server"

/**
 * Área logada: sem sessão vai para /entrar; com troca de senha pendente, para /trocar-senha;
 * o administrador vai para /admin.
 */
export default async function AppLayout({ children }: LayoutProps<"/">) {
  const { usuario, trocaObrigatoria } = await obterUsuarioSessao()
  if (trocaObrigatoria) redirect("/trocar-senha")
  if (!usuario) redirect("/entrar")
  // O administrador não vê dados financeiros (spec 004, FR-009): tem área própria.
  if (usuario.papel === "admin") redirect("/admin")
  const [jar, categorias, sugestaoSalario] = await Promise.all([
    cookies(),
    listarCategorias(),
    obterSugestaoSalario(),
  ])
  const menuAberto = jar.get("sidebar_state")?.value !== "false"
  return (
    <AppShell
      usuario={usuario}
      menuAberto={menuAberto}
      categorias={categorias}
      sugestaoSalario={sugestaoSalario}
    >
      {children}
    </AppShell>
  )
}
