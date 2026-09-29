import type { Metadata } from "next"

import { PageHeader } from "@/components/layout/page-header"
import { ListaCategorias } from "@/features/categorias/lista-categorias"
import { listarCategorias } from "@/lib/api/server"

export const metadata: Metadata = { title: "Categorias" }

export default async function CategoriasPage() {
  const categorias = await listarCategorias({ incluirInativas: true })
  return (
    <>
      <PageHeader
        titulo="Categorias"
        descricao="Organize para onde o dinheiro vai. Desativar tira a categoria das opções sem apagar o histórico."
      />
      <ListaCategorias categorias={categorias} />
    </>
  )
}
