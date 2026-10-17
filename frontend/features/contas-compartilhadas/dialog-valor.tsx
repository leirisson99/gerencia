"use client"

import { useState, type FormEvent } from "react"
import { useRouter } from "next/navigation"
import { toast } from "sonner"

import { BotaoEnviar } from "@/components/forms/botao-enviar"
import { Campo } from "@/components/forms/campo"
import { CampoValor } from "@/components/forms/campo-valor"
import { ErroForm } from "@/components/forms/erro-form"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { ApiError } from "@/lib/api/client"
import { editarValorDoParticipante } from "@/lib/api/contas-compartilhadas"
import type { ModoDivisao, ParticipanteDono } from "@/lib/api/types"
import { MENSAGEM_GENERICA } from "@/lib/forms"
import { bpsDeTexto, textoDeBps } from "./rotulos"

type Props = {
  aberto: boolean
  aoMudar: (aberto: boolean) => void
  contaId: number
  modo: Exclude<ModoDivisao, "igual">
  participante: ParticipanteDono
}

/** O dono ajusta a parte de uma pessoa (inclusive a dele). Vale a partir da próxima cobrança. */
export function DialogValor({ aberto, aoMudar, contaId, modo, participante }: Props) {
  return (
    <Dialog open={aberto} onOpenChange={aoMudar}>
      <DialogContent className="p-6 sm:max-w-md">
        <DialogHeader className="mb-2">
          <DialogTitle className="text-xl">Parte de {participante.nome ?? participante.email_convite}</DialogTitle>
          <DialogDescription>
            {modo === "percentual"
              ? "A soma de quem aceitou tem de dar 100% para a cobrança ser gerada."
              : "A soma de quem aceitou tem de dar o total para a cobrança ser gerada."}
          </DialogDescription>
        </DialogHeader>
        {aberto && (
          <FormValor
            contaId={contaId}
            modo={modo}
            participante={participante}
            aoConcluir={() => aoMudar(false)}
          />
        )}
      </DialogContent>
    </Dialog>
  )
}

function FormValor({
  contaId,
  modo,
  participante,
  aoConcluir,
}: {
  contaId: number
  modo: Exclude<ModoDivisao, "igual">
  participante: ParticipanteDono
  aoConcluir: () => void
}) {
  const router = useRouter()
  const [percentual, setPercentual] = useState(
    participante.valor === null ? "" : textoDeBps(participante.valor)
  )
  const [centavos, setCentavos] = useState(participante.valor ?? 0)
  const [erro, setErro] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)

  async function enviar(e: FormEvent) {
    e.preventDefault()
    setErro(null)
    let valor = centavos
    if (modo === "percentual") {
      const bps = bpsDeTexto(percentual)
      if (bps === null) return setErro("Informe um percentual de 0 a 100.")
      valor = bps
    }
    setEnviando(true)
    try {
      await editarValorDoParticipante(contaId, participante.id, valor)
      toast.success("Parte atualizada.")
      aoConcluir()
      router.refresh()
    } catch (e) {
      setErro(e instanceof ApiError ? e.message : MENSAGEM_GENERICA)
    } finally {
      setEnviando(false)
    }
  }

  return (
    <form onSubmit={enviar} noValidate>
      <div className="grid gap-5">
        {modo === "percentual" ? (
          <Campo
            label="Percentual"
            inputMode="decimal"
            autoFocus
            autoComplete="off"
            value={percentual}
            onChange={(e) => setPercentual(e.target.value)}
          />
        ) : (
          <CampoValor label="Valor" value={centavos} onChange={setCentavos} />
        )}
        <ErroForm mensagem={erro} />
        <div>
          <BotaoEnviar enviando={enviando}>Salvar</BotaoEnviar>
        </div>
      </div>
    </form>
  )
}
