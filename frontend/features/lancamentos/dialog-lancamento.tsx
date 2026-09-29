"use client"

import type { ReactNode } from "react"
import { useRouter } from "next/navigation"
import { toast } from "sonner"

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import type { Categoria, Lancamento } from "@/lib/api/types"
import { formatarData } from "@/lib/format"
import { FormLancamento } from "./form-lancamento"

type Props = {
  aberto: boolean
  aoMudar: (aberto: boolean) => void
  categorias: Categoria[]
  sugestaoSalario: number | null
  /** Presente ao editar. */
  lancamento?: Lancamento
  categoriaInicial?: Categoria
  /** Ações extras abaixo do formulário (ex.: excluir). */
  rodape?: ReactNode
}

/** Criar ou editar um lançamento. Ao salvar, fecha e recarrega os dados da página. */
export function DialogLancamento({
  aberto,
  aoMudar,
  categorias,
  sugestaoSalario,
  lancamento,
  categoriaInicial,
  rodape,
}: Props) {
  const router = useRouter()

  function aoConcluir(salvo: Lancamento) {
    aoMudar(false)
    if (lancamento) toast.success("Lançamento salvo.")
    else if (salvo.abre_ciclo) toast.success(`Salário lançado. Ciclo aberto em ${formatarData(salvo.data)}.`)
    else toast.success(`Lançado em ${formatarData(salvo.data)}.`)
    router.refresh()
  }

  return (
    <Dialog open={aberto} onOpenChange={aoMudar}>
      <DialogContent className="max-h-[calc(100dvh-2rem)] overflow-y-auto p-6 sm:max-w-md">
        <DialogHeader className="mb-2">
          <DialogTitle className="text-xl">{lancamento ? "Editar lançamento" : "Novo lançamento"}</DialogTitle>
          <DialogDescription>
            Só valor, categoria e data são obrigatórios. Entrada ou saída vem da categoria.
          </DialogDescription>
        </DialogHeader>
        {/* Monta de novo a cada abertura para começar sem valores e erros antigos. */}
        {aberto && (
          <FormLancamento
            categorias={categorias}
            sugestaoSalario={sugestaoSalario}
            lancamento={lancamento}
            categoriaInicial={categoriaInicial}
            aoConcluir={aoConcluir}
          />
        )}
        {rodape}
      </DialogContent>
    </Dialog>
  )
}
