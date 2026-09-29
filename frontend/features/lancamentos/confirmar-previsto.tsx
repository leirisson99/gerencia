"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { CheckIcon, Loader2Icon } from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { ApiError } from "@/lib/api/client"
import { editarLancamento } from "@/lib/api/lancamentos"
import type { Lancamento } from "@/lib/api/types"
import { MENSAGEM_GENERICA } from "@/lib/forms"
import { mostrarAvisoLimite } from "./aviso-limite"

/**
 * Marca um previsto como realizado, com o valor e a data que já tem.
 * Se algo mudou, a pessoa edita o lançamento antes (clicando nele).
 */
export function ConfirmarPrevisto({ lancamento, rotulo }: { lancamento: Lancamento; rotulo: string }) {
  const router = useRouter()
  const [enviando, setEnviando] = useState(false)

  async function confirmar() {
    setEnviando(true)
    try {
      const confirmado = await editarLancamento(lancamento.id, { status: "realizado" })
      toast.success(lancamento.tipo === "saida" ? "Pagamento confirmado." : "Recebimento confirmado.")
      mostrarAvisoLimite(confirmado.aviso_limite)
      router.refresh()
    } catch (e) {
      toast.error(e instanceof ApiError ? e.message : MENSAGEM_GENERICA)
    } finally {
      setEnviando(false)
    }
  }

  return (
    <Button variant="outline" size="sm" onClick={confirmar} disabled={enviando} aria-busy={enviando}>
      {enviando ? <Loader2Icon className="animate-spin" aria-hidden /> : <CheckIcon aria-hidden />}
      {rotulo}
    </Button>
  )
}
