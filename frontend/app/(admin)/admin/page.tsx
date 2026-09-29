import type { Metadata } from "next"
import Link from "next/link"
import { SearchIcon } from "lucide-react"

import { PageHeader } from "@/components/layout/page-header"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ResetarSenha } from "@/features/admin/resetar-senha"
import { listarUsuariosAdmin } from "@/lib/api/server"
import { formatarDataDeInstante } from "@/lib/format"

export const metadata: Metadata = { title: "Administração" }

/** Busca de contas e reset de senha: a única ação do administrador (constituição, papel admin). */
export default async function AdminPage({ searchParams }: PageProps<"/admin">) {
  const { busca: param } = await searchParams
  const busca = typeof param === "string" ? param.trim() : ""
  const usuarios = await listarUsuariosAdmin(busca || undefined)

  return (
    <>
      <PageHeader
        titulo="Contas"
        descricao="Encontre quem pediu ajuda para entrar e gere uma senha temporária. Dados financeiros não aparecem aqui."
      />

      {/* Formulário GET: a busca fica na URL e funciona sem JavaScript. */}
      <form role="search" className="mb-6 flex max-w-xl gap-2">
        <label htmlFor="busca" className="sr-only">
          Buscar por nome ou e-mail
        </label>
        <Input
          id="busca"
          name="busca"
          type="search"
          defaultValue={busca}
          placeholder="Buscar por nome ou e-mail"
          autoComplete="off"
        />
        <Button type="submit" variant="outline">
          <SearchIcon aria-hidden />
          Buscar
        </Button>
      </form>

      {usuarios.length === 0 ? (
        <p className="border-t py-8 text-muted-foreground">
          {busca ? (
            <>
              Nenhuma conta encontrada para &ldquo;{busca}&rdquo;.{" "}
              <Link href="/admin" className="underline underline-offset-4">
                Limpar busca
              </Link>
            </>
          ) : (
            "Nenhuma conta cadastrada ainda."
          )}
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[36rem] text-left">
            <caption className="sr-only">Contas de usuário</caption>
            <thead className="text-sm text-muted-foreground">
              <tr className="border-b">
                <th scope="col" className="py-3 pr-4 font-medium">Nome</th>
                <th scope="col" className="py-3 pr-4 font-medium">E-mail</th>
                <th scope="col" className="py-3 pr-4 font-medium">Criada em</th>
                <th scope="col" className="py-3 font-medium">
                  <span className="sr-only">Ações</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {usuarios.map((u) => (
                <tr key={u.id} className="border-b">
                  <td className="py-3 pr-4">{u.nome}</td>
                  <td className="py-3 pr-4 text-muted-foreground">{u.email}</td>
                  <td className="valor py-3 pr-4 text-muted-foreground">
                    {formatarDataDeInstante(u.criado_em)}
                  </td>
                  <td className="py-3 text-right">
                    <ResetarSenha usuario={u} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  )
}
