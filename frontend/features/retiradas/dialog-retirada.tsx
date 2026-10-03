"use client"

import { useState, type ReactNode } from "react"
import { useRouter } from "next/navigation"
import { Controller, useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { ArrowRightLeftIcon, Loader2Icon, Trash2Icon } from "lucide-react"
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
  DialogTrigger,
} from "@/components/ui/dialog"
import { FieldGroup } from "@/components/ui/field"
import { useCarteira } from "@/features/carteira/contexto"
import { ApiError } from "@/lib/api/client"
import { criarRetirada, editarRetirada, excluirRetirada } from "@/lib/api/retiradas"
import type { Lancamento } from "@/lib/api/types"
import { formatarCentavos, formatarData, hojeSaoPaulo } from "@/lib/format"
import { aplicarErroApi, MENSAGEM_GENERICA } from "@/lib/forms"

// Espelha backend/app/domain/retirada.py; a API segue como fonte da verdade.
const MAX_DESCRICAO = 200

const esquema = z.object({
  valor: z.number().int().min(1, "Informe um valor maior que zero."),
  data: z.string().min(1, "Informe a data."),
  descricao: z.string().trim().max(MAX_DESCRICAO, `Máximo de ${MAX_DESCRICAO} caracteres.`),
})

type Valores = z.infer<typeof esquema>

/** O que a tela já sabe da retirada a editar: vem de um dos dois lançamentos dela. */
export type RetiradaEditada = { id: number; valor: number; data: string; descricao: string | null }

export function retiradaDoLancamento(lancamento: Lancamento): RetiradaEditada | null {
  if (lancamento.retirada_id == null) return null
  return {
    id: lancamento.retirada_id,
    valor: lancamento.valor,
    data: lancamento.data,
    descricao: lancamento.descricao,
  }
}

function FormRetirada({ retirada, aoConcluir }: { retirada?: RetiradaEditada; aoConcluir: () => void }) {
  const router = useRouter()
  const [erroGeral, setErroGeral] = useState<string | null>(null)
  const hoje = hojeSaoPaulo()
  const form = useForm<Valores>({
    resolver: zodResolver(esquema),
    defaultValues: retirada
      ? { valor: retirada.valor, data: retirada.data, descricao: retirada.descricao ?? "" }
      : { valor: 0, data: hoje, descricao: "" },
  })
  const { errors, isSubmitting, isDirty } = form.formState

  async function enviar(valores: Valores) {
    setErroGeral(null)
    if (valores.data > hoje) {
      form.setError("data", { message: "A retirada é registrada quando acontece. Use hoje ou antes." })
      return
    }
    const dados = { valor: valores.valor, data: valores.data, descricao: valores.descricao || null }
    try {
      if (retirada) await editarRetirada(retirada.id, dados)
      else await criarRetirada(dados)
      toast.success(
        retirada
          ? "Retirada salva. A PJ e a PF mudaram juntas."
          : `Retirada de ${formatarCentavos(dados.valor)} registrada na PJ e na PF.`
      )
      aoConcluir()
      router.refresh()
    } catch (erro) {
      setErroGeral(
        aplicarErroApi(form, erro, { salario_necessario: "data", antes_do_primeiro_ciclo: "data" })
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
              label="Valor"
              autoFocus
              erro={errors.valor?.message}
              name={field.name}
              ref={field.ref}
              onBlur={field.onBlur}
              value={field.value}
              onChange={field.onChange}
            />
          )}
        />
        <Campo label="Data" type="date" max={hoje} erro={errors.data?.message} {...form.register("data")} />
        <Campo
          label="Descrição (opcional)"
          autoComplete="off"
          placeholder="Ex.: Pró-labore de outubro"
          maxLength={MAX_DESCRICAO}
          erro={errors.descricao?.message}
          {...form.register("descricao")}
        />
        <ErroForm mensagem={erroGeral} />
        <BotaoEnviar enviando={isSubmitting} disabled={Boolean(retirada) && !isDirty} className="w-full">
          {retirada ? "Salvar retirada" : "Retirar para PF"}
        </BotaoEnviar>
      </FieldGroup>
    </form>
  )
}

function ExcluirRetirada({ retirada, aoExcluir }: { retirada: RetiradaEditada; aoExcluir: () => void }) {
  const router = useRouter()
  const [excluindo, setExcluindo] = useState(false)
  const [erro, setErro] = useState<string | null>(null)

  async function excluir() {
    setErro(null)
    setExcluindo(true)
    try {
      await excluirRetirada(retirada.id)
      toast.success("Retirada excluída da PJ e da PF.")
      aoExcluir()
      router.refresh()
    } catch (e) {
      setErro(e instanceof ApiError ? e.message : MENSAGEM_GENERICA)
    } finally {
      setExcluindo(false)
    }
  }

  return (
    <div className="grid gap-2">
      <Button
        variant="ghost"
        className="justify-self-start text-destructive hover:text-destructive"
        onClick={excluir}
        disabled={excluindo}
      >
        {excluindo ? <Loader2Icon className="animate-spin" aria-hidden /> : <Trash2Icon aria-hidden />}
        Excluir retirada (PJ e PF)
      </Button>
      <ErroForm mensagem={erro} />
    </div>
  )
}

type Props = {
  /** Presente ao editar; sem ele, cria uma retirada nova. */
  retirada?: RetiradaEditada
  /** Controle externo (edição a partir da lista). Sem ele, o próprio botão abre. */
  aberto?: boolean
  aoMudar?: (aberto: boolean) => void
  /** Conteúdo do botão que abre, no modo sem controle externo. */
  children?: ReactNode
}

/**
 * Dinheiro da empresa para a pessoa: uma ação gera a saída na PJ e a entrada na PF, que só
 * mudam juntas. O botão só aparece na visão PJ.
 */
export function DialogRetirada({ retirada, aberto, aoMudar, children }: Props) {
  const { carteira } = useCarteira()
  const [abertoInterno, setAbertoInterno] = useState(false)
  const controlado = aberto !== undefined
  const estaAberto = controlado ? aberto : abertoInterno
  const mudar = controlado ? (aoMudar ?? (() => {})) : setAbertoInterno

  if (!controlado && carteira !== "pj") return null

  return (
    <Dialog open={estaAberto} onOpenChange={mudar}>
      {!controlado && (
        <DialogTrigger asChild>
          {children ?? (
            <Button variant="outline">
              <ArrowRightLeftIcon aria-hidden />
              Retirar para PF
            </Button>
          )}
        </DialogTrigger>
      )}
      <DialogContent className="max-h-[calc(100dvh-2rem)] overflow-y-auto p-6 sm:max-w-md">
        <DialogHeader className="mb-2">
          <DialogTitle className="text-xl">{retirada ? "Editar retirada" : "Retirar para PF"}</DialogTitle>
          <DialogDescription>
            {retirada
              ? `Retirada de ${formatarData(retirada.data)}. A saída na PJ e a entrada na PF mudam juntas.`
              : 'Sai da PJ como "Retirada para PF" e entra na PF como "Pró-labore e lucros".'}
          </DialogDescription>
        </DialogHeader>
        {estaAberto && <FormRetirada retirada={retirada} aoConcluir={() => mudar(false)} />}
        {estaAberto && retirada && <ExcluirRetirada retirada={retirada} aoExcluir={() => mudar(false)} />}
      </DialogContent>
    </Dialog>
  )
}
