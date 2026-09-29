import type { Metadata } from "next"
import { redirect } from "next/navigation"

import { PageHeader } from "@/components/layout/page-header"
import { Separator } from "@/components/ui/separator"
import { FormPerfil } from "@/features/perfil/form-perfil"
import { SecaoSenha } from "@/features/perfil/secao-senha"
import { obterUsuarioSessao } from "@/lib/api/server"

export const metadata: Metadata = { title: "Minha conta" }

/** Dados e senha do próprio administrador; reusa os formulários do Perfil. */
export default async function AdminContaPage() {
  const { usuario } = await obterUsuarioSessao()
  if (!usuario) redirect("/entrar")

  return (
    <div className="max-w-120">
      <PageHeader titulo="Minha conta" />
      <FormPerfil usuario={usuario} />
      <Separator className="my-12" />
      <h2 className="mb-6 text-xl">Senha</h2>
      <SecaoSenha />
    </div>
  )
}
