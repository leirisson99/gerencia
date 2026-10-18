import type { Metadata } from "next"

import { PageHeader } from "@/components/layout/page-header"
import { CartaoConta } from "@/features/contas-compartilhadas/cartao-conta"
import { ListaConvites } from "@/features/contas-compartilhadas/convites"
import { NovaConta } from "@/features/contas-compartilhadas/nova-conta"
import {
  listarCategorias,
  listarContasCompartilhadas,
  listarConvitesCompartilhados,
} from "@/lib/api/server"
import { obterCarteira } from "@/lib/carteira"

export const metadata: Metadata = { title: "Contas compartilhadas" }

export default async function ContasCompartilhadasPage() {
  // Contas compartilhadas existem só na carteira PF: a PJ não mostra a lista.
  if ((await obterCarteira()) === "pj") {
    return (
      <>
        <PageHeader titulo="Contas compartilhadas" />
        <p className="border-t py-8 text-muted-foreground">
          Contas compartilhadas existem só na carteira PF. Troque para PF no seletor para ver as suas.
        </p>
      </>
    )
  }

  const [contas, categorias, convites] = await Promise.all([
    listarContasCompartilhadas(),
    listarCategorias(),
    listarConvitesCompartilhados(),
  ])

  return (
    <>
      <div className="flex flex-wrap items-start justify-between gap-4">
        <PageHeader
          titulo="Contas compartilhadas"
          descricao="Aluguel, água, luz e outras contas que você divide com mais gente."
        />
        <NovaConta categorias={categorias} />
      </div>

      <ListaConvites convites={convites} categorias={categorias} />

      {contas.length === 0 ? (
        <p className="border-t py-8 text-muted-foreground">
          Nenhuma conta compartilhada. Cadastre o aluguel, a água ou a luz e convide quem divide com
          você: a parte de cada um vira um lançamento previsto no ciclo dele.
        </p>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {contas.map((c) => (
            <CartaoConta key={c.id} conta={c} />
          ))}
        </div>
      )}
    </>
  )
}
