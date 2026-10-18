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
import { gerarCobranca } from "@/lib/api/contas-compartilhadas"
import type { ContaDono } from "@/lib/api/types"
import { VALOR_MAXIMO, formatarCentavos, hojeSaoPaulo } from "@/lib/format"
import { MENSAGEM_GENERICA } from "@/lib/forms"
import { rotuloPessoas } from "./rotulos"

type Props = {
  aberto: boolean
  aoMudar: (aberto: boolean) => void
  conta: ContaDono
}

/** O dono fecha o mês: o total é dividido só entre quem já aceitou o convite. */
export function DialogCobranca({ aberto, aoMudar, conta }: Props) {
  return (
    <Dialog open={aberto} onOpenChange={aoMudar}>
      <DialogContent className="p-6 sm:max-w-md">
        <DialogHeader className="mb-2">
          <DialogTitle className="text-xl">Gerar cobrança</DialogTitle>
          <DialogDescription>
            O total é dividido entre as {rotuloPessoas(conta.qtd_pessoas)} que já aceitaram. Quem
            aceitar depois entra só na próxima cobrança, e a sua parte de cada um vira um lançamento
            previsto no ciclo dele.
          </DialogDescription>
        </DialogHeader>
        {aberto && <FormCobranca conta={conta} aoConcluir={() => aoMudar(false)} />}
      </DialogContent>
    </Dialog>
  )
}

function FormCobranca({ conta, aoConcluir }: { conta: ContaDono; aoConcluir: () => void }) {
  const router = useRouter()
  const [mes, setMes] = useState(hojeSaoPaulo().slice(0, 7))
  const [total, setTotal] = useState(0)
  const [erroMes, setErroMes] = useState<string | undefined>()
  const [erroTotal, setErroTotal] = useState<string | undefined>()
  const [erro, setErro] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)
  const fixo = conta.valor_fixo

  async function enviar(e: FormEvent) {
    e.preventDefault()
    setErro(null)
    setErroMes(undefined)
    setErroTotal(undefined)
    if (!/^\d{4}-\d{2}$/.test(mes)) return setErroMes("Escolha o mês.")
    if (fixo === null && total < 1) return setErroTotal("Informe o total deste mês.")
    if (total > VALOR_MAXIMO) return setErroTotal("Valor acima do limite.")
    setEnviando(true)
    try {
      await gerarCobranca(conta.id, {
        competencia: `${mes}-01`,
        valor_total: fixo === null ? total : null,
      })
      toast.success("Cobrança gerada.")
      aoConcluir()
      router.refresh()
    } catch (e) {
      if (e instanceof ApiError && (e.campos.valor_total || e.campos.competencia)) {
        setErroTotal(e.campos.valor_total)
        setErroMes(e.campos.competencia)
      } else {
        setErro(e instanceof ApiError ? e.message : MENSAGEM_GENERICA)
      }
    } finally {
      setEnviando(false)
    }
  }

  return (
    <form onSubmit={enviar} noValidate>
      <div className="grid gap-5">
        <Campo
          label="Mês"
          type="month"
          value={mes}
          onChange={(e) => setMes(e.target.value)}
          erro={erroMes}
        />
        {fixo === null ? (
          <CampoValor
            label="Total do mês"
            autoFocus
            value={total}
            onChange={setTotal}
            erro={erroTotal}
          />
        ) : (
          <Campo
            label="Total do mês"
            readOnly
            value={formatarCentavos(fixo)}
            descricao="Valor fixo da conta."
            erro={erroTotal}
          />
        )}
        <ErroForm mensagem={erro} />
        <div>
          <BotaoEnviar enviando={enviando}>Gerar cobrança</BotaoEnviar>
        </div>
      </div>
    </form>
  )
}
