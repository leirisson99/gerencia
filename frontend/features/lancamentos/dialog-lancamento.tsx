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
import type { Categoria, Lancamento, LancamentoComAviso, TipoLancamento } from "@/lib/api/types"
import { formatarData } from "@/lib/format"
import { mostrarAvisoLimite } from "./aviso-limite"
import { FormLancamento } from "./form-lancamento"

type Props = {
  aberto: boolean
  aoMudar: (aberto: boolean) => void
  categorias: Categoria[]
  sugestaoSalario: number | null
  /** Presente ao editar. */
  lancamento?: Lancamento
  categoriaInicial?: Categoria
  /** Lançamento novo só de entrada ou só de saída: filtra as categorias e ajusta o título. */
  tipo?: TipoLancamento
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
  tipo,
  rodape,
}: Props) {
  const router = useRouter()
  const titulo = lancamento
    ? "Editar lançamento"
    : tipo === "entrada"
      ? "Nova entrada"
      : tipo === "saida"
        ? "Nova saída"
        : "Novo lançamento"

  function aoConcluir(salvo: LancamentoComAviso) {
    aoMudar(false)
    if (lancamento) toast.success("Lançamento salvo.")
    else if (salvo.abre_ciclo) toast.success(`Salário lançado. Ciclo aberto em ${formatarData(salvo.data)}.`)
    else toast.success(`Lançado em ${formatarData(salvo.data)}.`)
    mostrarAvisoLimite(salvo.aviso_limite)
    router.refresh()
  }

  return (
    <Dialog open={aberto} onOpenChange={aoMudar}>
      <DialogContent className="max-h-[calc(100dvh-2rem)] overflow-y-auto p-6 sm:max-w-md">
        <DialogHeader className="mb-2">
          <DialogTitle className="text-xl">{titulo}</DialogTitle>
          <DialogDescription>
            Só valor, categoria e data são obrigatórios.
            {!tipo && " Entrada ou saída vem da categoria."}
          </DialogDescription>
        </DialogHeader>
        {/* Monta de novo a cada abertura para começar sem valores e erros antigos. */}
        {aberto && (
          <FormLancamento
            categorias={categorias}
            sugestaoSalario={sugestaoSalario}
            lancamento={lancamento}
            categoriaInicial={categoriaInicial}
            tipo={tipo}
            aoConcluir={aoConcluir}
          />
        )}
        {rodape}
      </DialogContent>
    </Dialog>
  )
}
