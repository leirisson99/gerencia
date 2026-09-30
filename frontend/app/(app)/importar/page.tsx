import type { Metadata } from "next"

import { PageHeader } from "@/components/layout/page-header"
import { ImportarExtrato } from "@/features/importacao/importar-extrato"
import { listarCategorias } from "@/lib/api/server"

export const metadata: Metadata = { title: "Importar extrato" }

export default async function ImportarPage() {
  const categorias = await listarCategorias()
  return (
    <>
      <PageHeader
        titulo="Importar extrato"
        descricao="Traga as movimentações do seu banco em OFX, CSV ou PDF. Você confere cada linha e escolhe a categoria antes de gravar; nada é importado duas vezes."
      />
      <ImportarExtrato categorias={categorias} />
    </>
  )
}
