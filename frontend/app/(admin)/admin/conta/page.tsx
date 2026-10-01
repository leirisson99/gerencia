import type { Metadata } from "next"
import { redirect } from "next/navigation"

import { PageHeader } from "@/components/layout/page-header"
import { obterUsuarioSessao } from "@/lib/api/server"

export const metadata: Metadata = { title: "Minha conta" }

/**
 * Dados do administrador, só para leitura: nome, e-mail e senha vêm do .env do servidor, que
 * sempre vence (a API recusa editar o perfil e trocar a senha dele).
 */
export default async function AdminContaPage() {
  const { usuario } = await obterUsuarioSessao()
  if (!usuario) redirect("/entrar")

  return (
    <div className="max-w-120">
      <PageHeader
        titulo="Minha conta"
        descricao="Nome, e-mail e senha do administrador são definidos na configuração do servidor."
      />
      <dl className="flex flex-col gap-5">
        <div>
          <dt className="text-sm text-muted-foreground">Nome</dt>
          <dd className="mt-1">{usuario.nome}</dd>
        </div>
        <div>
          <dt className="text-sm text-muted-foreground">E-mail</dt>
          <dd className="mt-1">{usuario.email}</dd>
        </div>
      </dl>
      <section className="mt-12 rounded-lg border p-5">
        <h2 className="mb-2 font-medium">Para trocar a senha ou o e-mail</h2>
        <ol className="list-decimal space-y-1 pl-5 text-sm text-muted-foreground">
          <li>
            No servidor, gere o hash da nova senha com{" "}
            <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-foreground">
              uv run python -m app.cli hash-senha
            </code>
            .
          </li>
          <li>
            Atualize <code className="font-mono text-foreground">ADMIN_SENHA_HASH</code> ou{" "}
            <code className="font-mono text-foreground">ADMIN_EMAIL</code> no{" "}
            <code className="font-mono text-foreground">.env</code>.
          </li>
          <li>Reinicie a API. As sessões abertas do administrador são encerradas.</li>
        </ol>
      </section>
    </div>
  )
}
