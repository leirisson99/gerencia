import type { Metadata } from "next"

import { PageHeader } from "@/components/layout/page-header"
import { ListaLembretes } from "@/features/lembretes/lista-lembretes"
import { listarCategorias, obterLembretes, obterSugestaoSalario } from "@/lib/api/server"

export const metadata: Metadata = { title: "Lembretes" }

/** O que vence nos próximos 3 dias e o que já passou da data. Destino das notificações. */
export default async function LembretesPage() {
  const [lembretes, categorias, sugestaoSalario] = await Promise.all([
    obterLembretes(),
    listarCategorias({ incluirInativas: true }),
    obterSugestaoSalario(),
  ])
  return (
    <>
      <PageHeader
        titulo="Lembretes"
        descricao="Contas a pagar e valores a receber previstos que já passaram da data ou vencem nos próximos 3 dias."
      />
      <ListaLembretes
        lembretes={lembretes}
        categorias={categorias}
        sugestaoSalario={sugestaoSalario}
      />
    </>
  )
}
