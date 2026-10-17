"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Loader2Icon, UserMinusIcon } from "lucide-react"
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
import { removerParticipante } from "@/lib/api/contas-compartilhadas"
import type { ParticipanteDono } from "@/lib/api/types"
import { MENSAGEM_GENERICA } from "@/lib/forms"

/** Tira uma pessoa da conta a partir da próxima cobrança, depois de confirmar. */
export function RemoverParticipante({
  contaId,
  participante,
}: {
  contaId: number
  participante: ParticipanteDono
}) {
  const router = useRouter()
  const [aberto, setAberto] = useState(false)
  const [removendo, setRemovendo] = useState(false)
  const [erro, setErro] = useState<string | null>(null)
  const nome = participante.nome ?? participante.email_convite ?? "esta pessoa"

  async function confirmar() {
    setErro(null)
    setRemovendo(true)
    try {
      await removerParticipante(contaId, participante.id)
      setAberto(false)
      toast.success("Pessoa removida.")
      router.refresh()
    } catch (e) {
      setErro(e instanceof ApiError ? e.message : MENSAGEM_GENERICA)
    } finally {
      setRemovendo(false)
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
        <Button variant="ghost" size="sm" className="text-destructive hover:text-destructive">
          <UserMinusIcon aria-hidden />
          Remover
        </Button>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Remover {nome}?</AlertDialogTitle>
          <AlertDialogDescription>
            A pessoa sai da divisão a partir da próxima cobrança. As cobranças que já foram geradas
            ficam como estão.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <ErroForm mensagem={erro} />
        <AlertDialogFooter>
          <AlertDialogCancel disabled={removendo}>Cancelar</AlertDialogCancel>
          <Button variant="destructive" onClick={confirmar} disabled={removendo} aria-busy={removendo}>
            {removendo && <Loader2Icon className="animate-spin" aria-hidden />}
            Remover
          </Button>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
