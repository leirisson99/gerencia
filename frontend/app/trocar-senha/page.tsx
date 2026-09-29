import type { Metadata } from "next"
import { redirect } from "next/navigation"

import { AuthShell } from "@/components/layout/auth-shell"
import { TrocaObrigatoria } from "@/features/auth/troca-obrigatoria"
import { obterUsuarioSessao } from "@/lib/api/server"

export const metadata: Metadata = { title: "Trocar senha" }

export default async function TrocarSenhaPage() {
  const { usuario, trocaObrigatoria } = await obterUsuarioSessao()
  if (usuario) redirect("/")
  if (!trocaObrigatoria) redirect("/entrar")

  return (
    <AuthShell
      titulo="Trocar senha"
      subtitulo="Sua senha foi redefinida. Escolha uma nova para continuar."
    >
      <TrocaObrigatoria />
    </AuthShell>
  )
}
