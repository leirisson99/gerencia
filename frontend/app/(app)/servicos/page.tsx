import type { Metadata } from "next"
import { redirect } from "next/navigation"

import { PageHeader } from "@/components/layout/page-header"
import { ListaServicos } from "@/features/servicos/lista-servicos"
import { listarCategorias, listarServicos, obterTipoRenda } from "@/lib/api/server"
import { temServicos } from "@/lib/tipo-renda"

export const metadata: Metadata = { title: "Serviços" }

/** Serviços a receber, só para quem presta serviço (a API responde 403 aos outros). */
export default async function ServicosPage() {
  if (!temServicos(await obterTipoRenda())) redirect("/")
  const [servicos, categorias] = await Promise.all([
    listarServicos(),
    listarCategorias({ incluirInativas: true }),
  ])
  return (
    <>
      <PageHeader
        titulo="Serviços"
        descricao="O que clientes ainda vão pagar. Cada serviço vira uma entrada prevista na data combinada e passa a contar no saldo quando você marca o recebimento."
      />
      <ListaServicos servicos={servicos} categorias={categorias} />
    </>
  )
}
