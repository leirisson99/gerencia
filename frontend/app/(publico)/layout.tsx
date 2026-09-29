import { redirect } from "next/navigation"

import { obterUsuarioSessao } from "@/lib/api/server"

/** Telas públicas: quem já tem sessão vai direto para a área logada. */
export default async function PublicoLayout({ children }: LayoutProps<"/">) {
  const { usuario, trocaObrigatoria } = await obterUsuarioSessao()
  if (trocaObrigatoria) redirect("/trocar-senha")
  if (usuario) redirect("/")
  return children
}
