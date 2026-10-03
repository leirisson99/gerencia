import type { Metadata } from "next"
import Link from "next/link"
import { notFound } from "next/navigation"
import { ArrowLeftIcon } from "lucide-react"

import { Button } from "@/components/ui/button"
import { DetalheContaAdmin } from "@/features/admin/detalhe-conta"
import { obterAtividadeConta } from "@/lib/api/server"

export const metadata: Metadata = { title: "Conta" }

/**
 * Uso de uma conta, sem conteúdo (constituição 6.0.0): acesso, contagens e linha do tempo.
 * Abrir esta página fica registrado nas ações do administrador.
 */
export default async function AdminContaPage({ params }: PageProps<"/admin/contas/[id]">) {
  const { id } = await params
  if (!/^\d+$/.test(id)) notFound()

  const atividade = await obterAtividadeConta(Number(id))
  if (!atividade) notFound()

  return (
    <section aria-labelledby="conta-titulo">
      <Button variant="ghost" size="sm" className="-ml-2 mb-4" asChild>
        <Link href="/admin/contas">
          <ArrowLeftIcon aria-hidden />
          Contas
        </Link>
      </Button>

      <DetalheContaAdmin detalhe={atividade.detalhe} eventos={atividade.eventos} />
    </section>
  )
}
