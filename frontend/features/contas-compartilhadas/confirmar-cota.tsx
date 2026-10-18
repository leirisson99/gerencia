"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { CheckIcon, Loader2Icon, Undo2Icon } from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { ApiError } from "@/lib/api/client"
import { confirmarCota, desfazerConfirmacao } from "@/lib/api/contas-compartilhadas"
import type { ParticipanteDono } from "@/lib/api/types"
import { MENSAGEM_GENERICA } from "@/lib/forms"

/**
 * O dono confirma o que recebeu de cada pessoa. Só aparece depois que a pessoa marcou a parte
 * como paga; confirmar ou desfazer nunca muda o lançamento nem o saldo de ninguém.
 */
export function ConfirmarCota({ participante }: { participante: ParticipanteDono }) {
  const router = useRouter()
  const [enviando, setEnviando] = useState(false)
  const { cota_id: cotaId, status_cota: status } = participante
  if (cotaId === null || (status !== "informado" && status !== "confirmado")) return null
  const confirmado = status === "confirmado"

  async function alternar() {
    if (cotaId === null) return
    setEnviando(true)
    try {
      if (confirmado) await desfazerConfirmacao(cotaId)
      else await confirmarCota(cotaId)
      toast.success(confirmado ? "Confirmação desfeita." : "Recebimento confirmado.")
      router.refresh()
    } catch (erro) {
      toast.error(erro instanceof ApiError ? erro.message : MENSAGEM_GENERICA)
    } finally {
      setEnviando(false)
    }
  }

  return (
    <Button variant="outline" size="sm" onClick={alternar} disabled={enviando} aria-busy={enviando}>
      {enviando ? (
        <Loader2Icon className="animate-spin" aria-hidden />
      ) : confirmado ? (
        <Undo2Icon aria-hidden />
      ) : (
        <CheckIcon aria-hidden />
      )}
      {confirmado ? "Desfazer confirmação" : "Confirmar recebimento"}
    </Button>
  )
}
