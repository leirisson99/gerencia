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
import { excluirServico } from "@/lib/api/servicos"
import type { Servico } from "@/lib/api/types"
import { MENSAGEM_GENERICA } from "@/lib/forms"
import { rotuloServico } from "./situacao"

/** Exclui um serviço não recebido, e a entrada prevista dele, depois de confirmar. */
export function ExcluirServico({ servico, aoExcluir }: { servico: Servico; aoExcluir: () => void }) {
  const router = useRouter()
  const [aberto, setAberto] = useState(false)
  const [excluindo, setExcluindo] = useState(false)
  const [erro, setErro] = useState<string | null>(null)

  async function confirmar() {
    setErro(null)
    setExcluindo(true)
    try {
      await excluirServico(servico.id)
      setAberto(false)
      aoExcluir()
      toast.success("Serviço excluído.")
      router.refresh()
    } catch (e) {
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
          Excluir serviço
        </Button>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Excluir serviço?</AlertDialogTitle>
          <AlertDialogDescription>
            {rotuloServico(servico)} e a entrada prevista dele serão excluídos. Não dá para desfazer.
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
