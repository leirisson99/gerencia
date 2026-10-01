"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { CheckIcon, Loader2Icon } from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { ApiError } from "@/lib/api/client"
import { editarLancamento } from "@/lib/api/lancamentos"
import { receberServico } from "@/lib/api/servicos"
import type { Lancamento } from "@/lib/api/types"
import { hojeSaoPaulo } from "@/lib/format"
import { MENSAGEM_GENERICA } from "@/lib/forms"
import { mostrarAvisoLimite } from "./aviso-limite"

/**
 * Marca um previsto como realizado, com o valor e a data que já tem.
 * Se algo mudou, a pessoa edita o lançamento antes (clicando nele).
 * A entrada de um serviço é recebida pelo serviço, com o valor combinado e sem data futura.
 */
export function ConfirmarPrevisto({ lancamento, rotulo }: { lancamento: Lancamento; rotulo: string }) {
  const router = useRouter()
  const [enviando, setEnviando] = useState(false)

  async function confirmar() {
    setEnviando(true)
    try {
      if (lancamento.servico_id != null) {
        const hoje = hojeSaoPaulo()
        await receberServico(lancamento.servico_id, {
          data: lancamento.data > hoje ? hoje : lancamento.data,
        })
        toast.success("Serviço recebido.")
        router.refresh()
        return
      }
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
