import { redirect } from "next/navigation"

import { AdminShell } from "@/components/layout/admin-shell"
import { obterUsuarioSessao } from "@/lib/api/server"

/** Área do administrador: exige sessão, troca de senha feita e papel admin. */
export default async function AdminLayout({ children }: LayoutProps<"/">) {
  const { usuario, trocaObrigatoria } = await obterUsuarioSessao()
  if (trocaObrigatoria) redirect("/trocar-senha")
  if (!usuario) redirect("/entrar")
  if (usuario.papel !== "admin") redirect("/")
  return <AdminShell usuario={usuario}>{children}</AdminShell>
}
