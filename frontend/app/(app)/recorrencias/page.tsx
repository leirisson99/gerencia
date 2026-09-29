import type { Metadata } from "next"

import { PageHeader } from "@/components/layout/page-header"
import { ListaRecorrencias } from "@/features/recorrencias/lista-recorrencias"
import { listarCategorias, listarRecorrencias } from "@/lib/api/server"

export const metadata: Metadata = { title: "Recorrências" }

export default async function RecorrenciasPage() {
  const [recorrencias, categorias] = await Promise.all([
    listarRecorrencias(),
    listarCategorias({ incluirInativas: true }),
  ])
  return (
    <>
      <PageHeader
        titulo="Recorrências"
        descricao="Gastos e rendas fixas. Cada ciclo aberto pelo salário já começa com elas previstas; é só confirmar quando pagar ou receber."
      />
      <ListaRecorrencias recorrencias={recorrencias} categorias={categorias} />
    </>
  )
}
