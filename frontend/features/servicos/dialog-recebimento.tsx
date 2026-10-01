"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Controller, useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { toast } from "sonner"
import { z } from "zod"

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
import { FieldGroup } from "@/components/ui/field"
import { receberServico } from "@/lib/api/servicos"
import type { Servico } from "@/lib/api/types"
import { VALOR_MAXIMO, formatarCentavos, hojeSaoPaulo } from "@/lib/format"
import { aplicarErroApi } from "@/lib/forms"
import { rotuloServico } from "./situacao"

const esquema = z.object({
  valor: z
    .number()
    .int()
    .min(1, "Informe um valor maior que zero.")
    .max(VALOR_MAXIMO, "Valor acima do limite."),
  data: z.string().min(1, "Campo obrigatório."),
})

type Valores = z.infer<typeof esquema>

type Props = {
  aberto: boolean
  aoMudar: (aberto: boolean) => void
  servico?: Servico
}

/** Marca o recebimento: a entrada prevista vira realizada com a data e o valor recebidos. */
export function DialogRecebimento({ aberto, aoMudar, servico }: Props) {
  return (
    <Dialog open={aberto} onOpenChange={aoMudar}>
      <DialogContent className="max-h-[calc(100dvh-2rem)] overflow-y-auto p-6 sm:max-w-md">
        <DialogHeader className="mb-2">
          <DialogTitle className="text-xl">Marcar recebimento</DialogTitle>
          <DialogDescription>
            {servico && `${rotuloServico(servico)}. `}A entrada passa a contar no saldo na data do
            recebimento.
          </DialogDescription>
        </DialogHeader>
        {aberto && servico && (
          <FormRecebimento servico={servico} aoConcluir={() => aoMudar(false)} />
        )}
      </DialogContent>
    </Dialog>
  )
}

function FormRecebimento({ servico, aoConcluir }: { servico: Servico; aoConcluir: () => void }) {
  const router = useRouter()
  const [erroGeral, setErroGeral] = useState<string | null>(null)
  const hoje = hojeSaoPaulo()
  const form = useForm<Valores>({
    resolver: zodResolver(esquema),
    defaultValues: { valor: servico.valor, data: hoje },
  })
  const { errors, isSubmitting } = form.formState

  async function enviar(valores: Valores) {
    setErroGeral(null)
    if (valores.data > hoje) {
      form.setError("data", { message: "O recebimento é marcado quando o dinheiro entra." })
      return
    }
    try {
      await receberServico(servico.id, {
        data: valores.data,
        // Sem valor, a API usa o combinado.
        ...(valores.valor !== servico.valor && { valor: valores.valor }),
      })
      toast.success("Serviço recebido.")
      aoConcluir()
      router.refresh()
    } catch (erro) {
      setErroGeral(
        aplicarErroApi(form, erro, {
          salario_necessario: "data",
          antes_do_primeiro_ciclo: "data",
        })
      )
    }
  }

  return (
    <form onSubmit={form.handleSubmit(enviar)} noValidate>
      <FieldGroup>
        <Controller
          control={form.control}
          name="valor"
          render={({ field }) => (
            <CampoValor
              label="Valor recebido"
              autoFocus
              descricao={`Combinado: ${formatarCentavos(servico.valor)}.`}
              erro={errors.valor?.message}
              name={field.name}
              ref={field.ref}
              onBlur={field.onBlur}
              value={field.value}
              onChange={field.onChange}
            />
          )}
        />
        <Campo
          label="Data do recebimento"
          type="date"
          max={hoje}
          erro={errors.data?.message}
          {...form.register("data")}
        />
        <ErroForm mensagem={erroGeral} />
        <div>
          <BotaoEnviar enviando={isSubmitting}>Marcar recebido</BotaoEnviar>
        </div>
      </FieldGroup>
    </form>
  )
}
