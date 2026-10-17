"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Controller, useForm, useWatch } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { toast } from "sonner"
import { z } from "zod"

import { BotaoEnviar } from "@/components/forms/botao-enviar"
import { Campo } from "@/components/forms/campo"
import { CampoCategoria } from "@/components/forms/campo-categoria"
import { CampoValor } from "@/components/forms/campo-valor"
import { ErroForm } from "@/components/forms/erro-form"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Field, FieldDescription, FieldLabel } from "@/components/ui/field"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { ApiError } from "@/lib/api/client"
import { convidarParticipante, criarContaCompartilhada } from "@/lib/api/contas-compartilhadas"
import type { Categoria, ModoDivisao } from "@/lib/api/types"
import { VALOR_MAXIMO } from "@/lib/format"
import { aplicarErroApi, regras } from "@/lib/forms"
import { DESCRICAO_MODOS, MODOS } from "./rotulos"

// Espelha backend/app/schemas/conta_compartilhada.py; a API segue como fonte da verdade.
const MAX_DESCRICAO = 200

const SEPARADOR_EMAILS = /[\s,;]+/

/** E-mails digitados, sem repetição, em minúsculas. */
function emailsDoTexto(texto: string): string[] {
  const todos = texto
    .split(SEPARADOR_EMAILS)
    .map((e) => e.trim().toLowerCase())
    .filter(Boolean)
  return [...new Set(todos)]
}

const esquema = z.object({
  descricao: regras.obrigatorio(MAX_DESCRICAO),
  categoria_id: z.string().min(1, "Escolha uma categoria."),
  modo: z.enum(["igual", "percentual", "fixo"]),
  dia_vencimento: regras.diaDoMes,
  valor_fixo: z.number().int().min(0).max(VALOR_MAXIMO, "Valor acima do limite."),
  emails: z.string().refine((v) => emailsDoTexto(v).every((e) => z.email().safeParse(e).success), {
    message: "Confira os e-mails: separe por vírgula ou espaço.",
  }),
})

type Valores = z.infer<typeof esquema>

type Props = {
  aberto: boolean
  aoMudar: (aberto: boolean) => void
  /** Só as ativas. */
  categorias: Categoria[]
}

export function DialogConta({ aberto, aoMudar, categorias }: Props) {
  return (
    <Dialog open={aberto} onOpenChange={aoMudar}>
      <DialogContent className="max-h-[calc(100dvh-2rem)] overflow-y-auto p-6 sm:max-w-lg">
        <DialogHeader className="mb-2">
          <DialogTitle className="text-xl">Nova conta compartilhada</DialogTitle>
          <DialogDescription>
            Aluguel, água, luz... Cada pessoa que aceitar o convite paga a sua parte, e a parte dela vira
            um lançamento previsto no ciclo dela.
          </DialogDescription>
        </DialogHeader>
        {/* Monta de novo a cada abertura para começar sem valores e erros antigos. */}
        {aberto && <FormConta categorias={categorias} aoConcluir={() => aoMudar(false)} />}
      </DialogContent>
    </Dialog>
  )
}

function FormConta({ categorias, aoConcluir }: { categorias: Categoria[]; aoConcluir: () => void }) {
  const router = useRouter()
  const [erroGeral, setErroGeral] = useState<string | null>(null)
  const form = useForm<Valores>({
    resolver: zodResolver(esquema),
    defaultValues: {
      descricao: "",
      categoria_id: "",
      modo: "igual",
      dia_vencimento: "",
      valor_fixo: 0,
      emails: "",
    },
  })
  const { errors, isSubmitting } = form.formState
  const modo = useWatch({ control: form.control, name: "modo" })

  async function enviar(v: Valores) {
    setErroGeral(null)
    let conta
    try {
      conta = await criarContaCompartilhada({
        descricao: v.descricao,
        categoria_id: Number(v.categoria_id),
        modo: v.modo,
        dia_vencimento: Number(v.dia_vencimento),
        valor_fixo: v.valor_fixo > 0 ? v.valor_fixo : null,
      })
    } catch (erro) {
      setErroGeral(aplicarErroApi(form, erro))
      return
    }

    // A conta já existe: um convite que falhe não a desfaz, só avisa.
    const emails = emailsDoTexto(v.emails)
    const recusados: string[] = []
    for (const email of emails) {
      try {
        await convidarParticipante(conta.id, { email })
      } catch (erro) {
        recusados.push(erro instanceof ApiError ? erro.message : email)
      }
    }
    toast.success(
      emails.length > 0 && recusados.length === 0
        ? "Conta criada e convites enviados."
        : "Conta criada."
    )
    if (recusados.length > 0) {
      toast.error(`Alguns convites não foram enviados: ${recusados[0]}`)
    }
    aoConcluir()
    router.push(`/contas-compartilhadas/${conta.id}`)
    router.refresh()
  }

  return (
    <form onSubmit={form.handleSubmit(enviar)} noValidate>
      <div className="grid gap-5">
        <Campo
          label="Descrição"
          autoFocus
          autoComplete="off"
          placeholder="Ex.: Energia"
          maxLength={MAX_DESCRICAO}
          erro={errors.descricao?.message}
          {...form.register("descricao")}
        />

        <Controller
          control={form.control}
          name="categoria_id"
          render={({ field }) => (
            <CampoCategoria
              categorias={categorias}
              tipo="saida"
              semSalario
              name={field.name}
              ref={field.ref}
              value={field.value}
              onBlur={field.onBlur}
              onChange={field.onChange}
              erro={errors.categoria_id?.message}
              descricao="A sua parte entra nesta categoria."
            />
          )}
        />

        <div className="grid gap-5 sm:grid-cols-2">
          <Campo
            label="Dia do vencimento"
            type="number"
            inputMode="numeric"
            min={1}
            max={31}
            erro={errors.dia_vencimento?.message}
            {...form.register("dia_vencimento")}
          />
          <Controller
            control={form.control}
            name="valor_fixo"
            render={({ field }) => (
              <CampoValor
                label="Valor fixo do mês"
                erro={errors.valor_fixo?.message}
                descricao="Deixe zerado se o valor muda todo mês (água, luz)."
                name={field.name}
                ref={field.ref}
                onBlur={field.onBlur}
                value={field.value}
                onChange={field.onChange}
              />
            )}
          />
        </div>

        <Controller
          control={form.control}
          name="modo"
          render={({ field }) => (
            <Field>
              <FieldLabel htmlFor="conta-modo">Como dividir</FieldLabel>
              <Select name={field.name} value={field.value} onValueChange={field.onChange}>
                <SelectTrigger id="conta-modo" ref={field.ref} className="w-full text-base data-[size=default]:h-10">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent position="popper">
                  {(Object.keys(MODOS) as ModoDivisao[]).map((m) => (
                    <SelectItem key={m} value={m}>
                      {MODOS[m]}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <FieldDescription>{DESCRICAO_MODOS[modo]}</FieldDescription>
            </Field>
          )}
        />

        <Campo
          label="Convidados (opcional)"
          autoComplete="off"
          placeholder="ana@email.com, bia@email.com"
          erro={errors.emails?.message}
          descricao={
            modo === "igual"
              ? "A conta só divide entre quem aceitar o convite."
              : "Depois de criar, defina a parte de cada pessoa na página da conta."
          }
          {...form.register("emails")}
        />

        <ErroForm mensagem={erroGeral} />
        <div>
          <BotaoEnviar enviando={isSubmitting}>Criar conta</BotaoEnviar>
        </div>
      </div>
    </form>
  )
}
