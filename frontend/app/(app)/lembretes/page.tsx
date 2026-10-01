import type { Metadata } from "next"

import { PageHeader } from "@/components/layout/page-header"
import { ListaLembretes } from "@/features/lembretes/lista-lembretes"
import { NovoLembrete } from "@/features/lembretes/lista-livres"
import {
  listarCategorias,
  listarLembretesLivres,
  obterLembretes,
  obterSugestaoSalario,
} from "@/lib/api/server"

export const metadata: Metadata = { title: "Lembretes" }

/** O que vence nos próximos 3 dias, o que já passou da data e os lembretes livres. */
export default async function LembretesPage() {
  const [lembretes, livres, categorias, sugestaoSalario] = await Promise.all([
    obterLembretes(),
    listarLembretesLivres(),
    listarCategorias({ incluirInativas: true }),
    obterSugestaoSalario(),
  ])
  return (
    <>
      <PageHeader
        titulo="Lembretes"
        descricao="Contas a pagar, valores a receber e lembretes que já passaram da data ou vencem nos próximos 3 dias."
      />
      <div className="mb-6 flex justify-end">
        <NovoLembrete />
      </div>
      <ListaLembretes
        lembretes={lembretes}
        livres={livres}
        categorias={categorias}
        sugestaoSalario={sugestaoSalario}
      />
    </>
  )
}
