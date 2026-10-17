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
import { convidarParticipante } from "@/lib/api/contas-compartilhadas"
import type { ModoDivisao } from "@/lib/api/types"
import { MENSAGEM_GENERICA } from "@/lib/forms"
import { bpsDeTexto } from "./rotulos"

type Props = {
  aberto: boolean
  aoMudar: (aberto: boolean) => void
  contaId: number
  modo: ModoDivisao
}

/** Convida uma pessoa por e-mail; a resposta é a mesma exista conta para o e-mail ou não. */
export function DialogConvite({ aberto, aoMudar, contaId, modo }: Props) {
  return (
    <Dialog open={aberto} onOpenChange={aoMudar}>
      <DialogContent className="p-6 sm:max-w-md">
        <DialogHeader className="mb-2">
          <DialogTitle className="text-xl">Convidar pessoa</DialogTitle>
          <DialogDescription>
            Ela só entra na divisão depois de aceitar o convite, e vale a partir da próxima cobrança.
          </DialogDescription>
        </DialogHeader>
        {aberto && <FormConvite contaId={contaId} modo={modo} aoConcluir={() => aoMudar(false)} />}
      </DialogContent>
    </Dialog>
  )
}

function FormConvite({
  contaId,
  modo,
  aoConcluir,
}: {
  contaId: number
  modo: ModoDivisao
  aoConcluir: () => void
}) {
  const router = useRouter()
  const [email, setEmail] = useState("")
  const [percentual, setPercentual] = useState("")
  const [centavos, setCentavos] = useState(0)
  const [erro, setErro] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)

  async function enviar(e: FormEvent) {
    e.preventDefault()
    setErro(null)
    let valor: number | null = null
    if (modo === "percentual") {
      valor = bpsDeTexto(percentual)
      if (valor === null) return setErro("Informe um percentual de 0 a 100.")
    } else if (modo === "fixo") {
      valor = centavos
    }
    setEnviando(true)
    try {
      await convidarParticipante(contaId, { email, valor })
      toast.success("Convite enviado.")
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
        <Campo
          label="E-mail"
          type="email"
          autoFocus
          autoComplete="off"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        {modo === "percentual" && (
          <Campo
            label="Percentual da pessoa"
            inputMode="decimal"
            autoComplete="off"
            placeholder="Ex.: 25"
            value={percentual}
            onChange={(e) => setPercentual(e.target.value)}
          />
        )}
        {modo === "fixo" && <CampoValor label="Valor da pessoa" value={centavos} onChange={setCentavos} />}
        <ErroForm mensagem={erro} />
        <div>
          <BotaoEnviar enviando={enviando}>Enviar convite</BotaoEnviar>
        </div>
      </div>
    </form>
  )
}
