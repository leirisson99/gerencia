"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Controller, useForm, useWatch } from "react-hook-form"
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
import { Field, FieldGroup, FieldLabel } from "@/components/ui/field"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { criarCategoria, editarCategoria } from "@/lib/api/categorias"
import type { Categoria, CategoriaPatch, TipoLancamento } from "@/lib/api/types"
import { VALOR_MAXIMO } from "@/lib/format"
import { aplicarErroApi, regras } from "@/lib/forms"

// Espelha MAX_NOME_CATEGORIA de backend/app/schemas/categoria.py.
const MAX_NOME = 60

const esquema = z.object({
  nome: regras.obrigatorio(MAX_NOME),
  tipo: z.enum(["entrada", "saida"]),
  /** 0 = sem limite (vira `null` ao enviar). */
  limite: z.number().int().min(0).max(VALOR_MAXIMO, "Valor acima do limite."),
})

type Valores = z.infer<typeof esquema>

type Props = {
  aberto: boolean
  aoMudar: (aberto: boolean) => void
  /** Presente ao editar; o tipo não muda depois de criada. */
  categoria?: Categoria
  tipoInicial?: TipoLancamento
}

export function DialogCategoria({ aberto, aoMudar, categoria, tipoInicial = "saida" }: Props) {
  return (
    <Dialog open={aberto} onOpenChange={aoMudar}>
      <DialogContent className="p-6 sm:max-w-md">
        <DialogHeader className="mb-2">
          <DialogTitle className="text-xl">{categoria ? "Editar categoria" : "Nova categoria"}</DialogTitle>
          <DialogDescription>
            {categoria
              ? "Os lançamentos já feitos passam a aparecer com o novo nome."
              : "O tipo define se os lançamentos nela são entradas ou saídas, e não muda depois."}
          </DialogDescription>
        </DialogHeader>
        {/* Monta de novo a cada abertura para começar sem valores e erros antigos. */}
        {aberto && (
          <FormCategoria categoria={categoria} tipoInicial={tipoInicial} aoConcluir={() => aoMudar(false)} />
        )}
      </DialogContent>
    </Dialog>
  )
}

function FormCategoria({
  categoria,
  tipoInicial,
  aoConcluir,
}: {
  categoria?: Categoria
  tipoInicial: TipoLancamento
  aoConcluir: () => void
}) {
  const router = useRouter()
  const [erroGeral, setErroGeral] = useState<string | null>(null)
  const form = useForm<Valores>({
    resolver: zodResolver(esquema),
    defaultValues: {
      nome: categoria?.nome ?? "",
      tipo: categoria?.tipo ?? tipoInicial,
      limite: categoria?.limite ?? 0,
    },
  })
  const { errors, isSubmitting, isDirty } = form.formState
  const tipo = useWatch({ control: form.control, name: "tipo" })
  // Categorias do sistema não mudam de nome, mas as de saída aceitam limite.
  const nomeTravado = categoria?.sistema ?? false

  async function enviar(valores: Valores) {
    setErroGeral(null)
    const limite = valores.tipo === "saida" && valores.limite > 0 ? valores.limite : null
    try {
      if (categoria) {
        const mudancas: CategoriaPatch = {}
        if (!nomeTravado && valores.nome !== categoria.nome) mudancas.nome = valores.nome
        if (limite !== categoria.limite) mudancas.limite = limite
        await editarCategoria(categoria.id, mudancas)
      } else {
        await criarCategoria({ nome: valores.nome, tipo: valores.tipo, limite })
      }
      toast.success(categoria ? "Categoria salva." : "Categoria criada.")
      aoConcluir()
      router.refresh()
    } catch (erro) {
      setErroGeral(aplicarErroApi(form, erro, { categoria_existente: "nome" }))
    }
  }

  return (
    <form onSubmit={form.handleSubmit(enviar)} noValidate>
      <FieldGroup>
        <Campo
          label="Nome"
          autoFocus={!nomeTravado}
          autoComplete="off"
          maxLength={MAX_NOME}
          disabled={nomeTravado}
          descricao={nomeTravado ? "Categoria do sistema: o nome não muda." : undefined}
          erro={errors.nome?.message}
          {...form.register("nome")}
        />
        {!categoria && (
          <Controller
            control={form.control}
            name="tipo"
            render={({ field }) => (
              <Field>
                <FieldLabel htmlFor="categoria-tipo">Tipo</FieldLabel>
                <Select name={field.name} value={field.value} onValueChange={field.onChange}>
                  <SelectTrigger
                    id="categoria-tipo"
                    ref={field.ref}
                    className="w-full text-base data-[size=default]:h-10"
                  >
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent position="popper">
                    <SelectItem value="saida">Saída</SelectItem>
                    <SelectItem value="entrada">Entrada</SelectItem>
                  </SelectContent>
                </Select>
              </Field>
            )}
          />
        )}
        {tipo === "saida" && (
          <Controller
            control={form.control}
            name="limite"
            render={({ field }) => (
              <CampoValor
                label="Limite por ciclo"
                descricao="Opcional. Você é avisado aos 80% e ao passar do limite; nada é bloqueado. Deixe em 0,00 para não ter limite."
                erro={errors.limite?.message}
                name={field.name}
                ref={field.ref}
                onBlur={field.onBlur}
                value={field.value}
                onChange={field.onChange}
              />
            )}
          />
        )}
        <ErroForm mensagem={erroGeral} />
        <div>
          <BotaoEnviar enviando={isSubmitting} disabled={Boolean(categoria) && !isDirty}>
            {categoria ? "Salvar" : "Criar categoria"}
          </BotaoEnviar>
        </div>
      </FieldGroup>
    </form>
  )
}
