"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Loader2Icon, Trash2Icon } from "lucide-react"
import { toast } from "sonner"

import { ErroForm } from "@/components/forms/erro-form"
import {
  AlertDialog,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog"
import { Button } from "@/components/ui/button"
import { ApiError } from "@/lib/api/client"
import { excluirLancamento } from "@/lib/api/lancamentos"
import type { Lancamento } from "@/lib/api/types"
import { MENSAGEM_GENERICA } from "@/lib/forms"

type Props = {
  lancamento: Lancamento
  /** Como o lançamento aparece na confirmação (ex.: "Mercado de 05/10/2026"). */
  rotulo: string
  aoExcluir: () => void
}

/** Exclui um lançamento depois de confirmar. */
export function ExcluirLancamento({ lancamento, rotulo, aoExcluir }: Props) {
  const router = useRouter()
  const [aberto, setAberto] = useState(false)
  const [excluindo, setExcluindo] = useState(false)
  const [erro, setErro] = useState<string | null>(null)

  async function confirmar() {
    setErro(null)
    setExcluindo(true)
    try {
      await excluirLancamento(lancamento.id)
      setAberto(false)
      aoExcluir()
      toast.success("Lançamento excluído.")
      router.refresh()
    } catch (e) {
      // `lancamentos_sem_ciclo` já explica por que o salário não pode sair.
      setErro(e instanceof ApiError ? e.message : MENSAGEM_GENERICA)
    } finally {
      setExcluindo(false)
    }
  }

  return (
    <AlertDialog
      open={aberto}
      onOpenChange={(abrir) => {
        setAberto(abrir)
        if (!abrir) setErro(null)
      }}
    >
      <AlertDialogTrigger asChild>
        <Button variant="ghost" className="justify-self-start text-destructive hover:text-destructive">
          <Trash2Icon aria-hidden />
          Excluir lançamento
        </Button>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Excluir lançamento?</AlertDialogTitle>
          <AlertDialogDescription>
            {rotulo} será excluído. {lancamento.abre_ciclo && "Como é um salário, os ciclos se reorganizam. "}
            Não dá para desfazer.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <ErroForm mensagem={erro} />
        <AlertDialogFooter>
          <AlertDialogCancel disabled={excluindo}>Cancelar</AlertDialogCancel>
          {/* Botão comum: a ação da Radix fecharia o dialog antes da resposta da API. */}
          <Button variant="destructive" onClick={confirmar} disabled={excluindo} aria-busy={excluindo}>
            {excluindo && <Loader2Icon className="animate-spin" aria-hidden />}
            Excluir
          </Button>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
