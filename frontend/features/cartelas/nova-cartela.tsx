"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { PlusIcon } from "lucide-react"
import { Controller, useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { toast } from "sonner"
import { z } from "zod"

import { BotaoEnviar } from "@/components/forms/botao-enviar"
import { Campo } from "@/components/forms/campo"
import { CampoValor } from "@/components/forms/campo-valor"
import { ErroForm } from "@/components/forms/erro-form"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { FieldGroup } from "@/components/ui/field"
import { criarCartela } from "@/lib/api/cartelas"
import { VALOR_MAXIMO } from "@/lib/format"
import { aplicarErroApi, regras } from "@/lib/forms"

// Espelha backend/app/schemas/cartela.py; o número de casas e o ajuste são calculados pela API.
const MAX_NOME = 80
const BASE_PADRAO = 100

const valor = z
  .number()
  .int()
  .min(1, "Informe um valor maior que zero.")
  .max(VALOR_MAXIMO, "Valor acima do limite.")

const esquema = z.object({
  nome: regras.obrigatorio(MAX_NOME),
  meta: valor,
  valor_base: valor,
})

type Valores = z.infer<typeof esquema>

/** Botão e dialog de cartela nova; ao criar, abre a grade de casas. */
export function NovaCartela() {
  const [aberto, setAberto] = useState(false)
  return (
    <>
      {/* No celular vira botão redondo só com o ícone, ao lado do título. */}
      <Button
        onClick={() => setAberto(true)}
        className="max-md:size-10 max-md:shrink-0 max-md:rounded-full max-md:p-0"
      >
        <PlusIcon aria-hidden />
        <span className="max-md:sr-only">Nova cartela</span>
      </Button>
      <Dialog open={aberto} onOpenChange={setAberto}>
        <DialogContent className="p-6 sm:max-w-md">
          <DialogHeader className="mb-2">
            <DialogTitle className="text-xl">Nova cartela</DialogTitle>
            <DialogDescription>
              A meta vira casas de valor crescente (base, 2× base, 3× base…) mais uma casa de ajuste
              que fecha o total. Deposite em qualquer ordem, no seu ritmo.
            </DialogDescription>
          </DialogHeader>
          {/* Monta de novo a cada abertura para começar sem valores e erros antigos. */}
          {aberto && <FormCartela aoConcluir={() => setAberto(false)} />}
        </DialogContent>
      </Dialog>
    </>
  )
}

function FormCartela({ aoConcluir }: { aoConcluir: () => void }) {
  const router = useRouter()
  const [erroGeral, setErroGeral] = useState<string | null>(null)
  const form = useForm<Valores>({
    resolver: zodResolver(esquema),
    defaultValues: { nome: "", meta: 0, valor_base: BASE_PADRAO },
  })
  const { errors, isSubmitting } = form.formState

  async function enviar(valores: Valores) {
    setErroGeral(null)
    try {
      const cartela = await criarCartela(valores)
      toast.success(`Cartela criada com ${cartela.casas.length} casas.`)
      aoConcluir()
      router.push(`/cartelas/${cartela.id}`)
      router.refresh()
    } catch (erro) {
      setErroGeral(aplicarErroApi(form, erro))
    }
  }

  return (
    <form onSubmit={form.handleSubmit(enviar)} noValidate>
      <FieldGroup>
        <Campo
          label="Nome"
          autoFocus
          autoComplete="off"
          placeholder="Ex.: Viagem"
          maxLength={MAX_NOME}
          erro={errors.nome?.message}
          {...form.register("nome")}
        />
        <div className="grid gap-5 sm:grid-cols-2">
          <Controller
            control={form.control}
            name="meta"
            render={({ field }) => (
              <CampoValor
                label="Meta"
                erro={errors.meta?.message}
                name={field.name}
                ref={field.ref}
                onBlur={field.onBlur}
                value={field.value}
                onChange={field.onChange}
              />
            )}
          />
          <Controller
            control={form.control}
            name="valor_base"
            render={({ field }) => (
              <CampoValor
                label="Valor base"
                descricao="Valor da primeira casa."
                erro={errors.valor_base?.message}
                name={field.name}
                ref={field.ref}
                onBlur={field.onBlur}
                value={field.value}
                onChange={field.onChange}
              />
            )}
          />
        </div>
        <ErroForm mensagem={erroGeral} />
        <div>
          <BotaoEnviar enviando={isSubmitting}>Criar cartela</BotaoEnviar>
        </div>
      </FieldGroup>
    </form>
  )
}
