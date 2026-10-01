"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { Loader2Icon, Trash2Icon } from "lucide-react"
import { toast } from "sonner"
import { z } from "zod"

import { BotaoEnviar } from "@/components/forms/botao-enviar"
import { Campo } from "@/components/forms/campo"
import { ErroForm } from "@/components/forms/erro-form"
import {
  AlertDialog,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { FieldGroup } from "@/components/ui/field"
import { ApiError } from "@/lib/api/client"
import {
  criarLembreteLivre,
  editarLembreteLivre,
  excluirLembreteLivre,
} from "@/lib/api/lembretes"
import type { LembreteLivre } from "@/lib/api/types"
import { formatarData, hojeSaoPaulo } from "@/lib/format"
import { MENSAGEM_GENERICA, aplicarErroApi, regras } from "@/lib/forms"

// Espelha backend/app/schemas/lembrete.py; a API segue como fonte da verdade.
const MAX_TEXTO = 200

const esquema = z.object({
  texto: regras.obrigatorio(MAX_TEXTO),
  data: z.string().min(1, "Campo obrigatório."),
})

type Valores = z.infer<typeof esquema>

type Props = {
  aberto: boolean
  aoMudar: (aberto: boolean) => void
  /** Presente ao editar. */
  lembrete?: LembreteLivre
}

/** Criar ou editar um lembrete livre (texto e data). Ao editar, também dá para excluir. */
export function DialogLembreteLivre({ aberto, aoMudar, lembrete }: Props) {
  return (
    <Dialog open={aberto} onOpenChange={aoMudar}>
      <DialogContent className="max-h-[calc(100dvh-2rem)] overflow-y-auto p-6 sm:max-w-md">
        <DialogHeader className="mb-2">
          <DialogTitle className="text-xl">{lembrete ? "Editar lembrete" : "Novo lembrete"}</DialogTitle>
          <DialogDescription>
            Aparece em Lembretes e no resumo das 8h a partir de 3 dias antes da data. O texto não
            vai na notificação.
          </DialogDescription>
        </DialogHeader>
        {/* Monta de novo a cada abertura para começar sem valores e erros antigos. */}
        {aberto && <FormLembreteLivre lembrete={lembrete} aoConcluir={() => aoMudar(false)} />}
        {lembrete && <ExcluirLembreteLivre lembrete={lembrete} aoExcluir={() => aoMudar(false)} />}
      </DialogContent>
    </Dialog>
  )
}

function FormLembreteLivre({
  lembrete,
  aoConcluir,
}: {
  lembrete?: LembreteLivre
  aoConcluir: () => void
}) {
  const router = useRouter()
  const [erroGeral, setErroGeral] = useState<string | null>(null)
  const form = useForm<Valores>({
    resolver: zodResolver(esquema),
    defaultValues: lembrete
      ? { texto: lembrete.texto, data: lembrete.data }
      : { texto: "", data: hojeSaoPaulo() },
  })
  const { errors, isSubmitting, isDirty } = form.formState

  async function enviar(valores: Valores) {
    setErroGeral(null)
    try {
      if (lembrete) {
        await editarLembreteLivre(lembrete.id, valores)
        toast.success("Lembrete salvo.")
      } else {
        const criado = await criarLembreteLivre(valores)
        toast.success(`Lembrete para ${formatarData(criado.data)}.`)
      }
      aoConcluir()
      router.refresh()
    } catch (erro) {
      setErroGeral(aplicarErroApi(form, erro))
    }
  }

  return (
    <form onSubmit={form.handleSubmit(enviar)} noValidate>
      <FieldGroup>
        <Campo
          label="Lembrete"
          autoFocus
          autoComplete="off"
          placeholder="Ex.: Renovar o seguro do carro"
          maxLength={MAX_TEXTO}
          erro={errors.texto?.message}
          {...form.register("texto")}
        />
        <Campo label="Data" type="date" erro={errors.data?.message} {...form.register("data")} />
        <ErroForm mensagem={erroGeral} />
        <div>
          <BotaoEnviar enviando={isSubmitting} disabled={Boolean(lembrete) && !isDirty}>
            {lembrete ? "Salvar alterações" : "Criar lembrete"}
          </BotaoEnviar>
        </div>
      </FieldGroup>
    </form>
  )
}

function ExcluirLembreteLivre({
  lembrete,
  aoExcluir,
}: {
  lembrete: LembreteLivre
  aoExcluir: () => void
}) {
  const router = useRouter()
  const [aberto, setAberto] = useState(false)
  const [excluindo, setExcluindo] = useState(false)
  const [erro, setErro] = useState<string | null>(null)

  async function confirmar() {
    setErro(null)
    setExcluindo(true)
    try {
      await excluirLembreteLivre(lembrete.id)
      setAberto(false)
      aoExcluir()
      toast.success("Lembrete excluído.")
      router.refresh()
    } catch (e) {
      setErro(e instanceof ApiError ? e.message : MENSAGEM_GENERICA)
    } finally {
      setExcluindo(false)
    }
  }

  return (
    <AlertDialog
      open={aberto}
      onOpenChange={(abrir) => {
        setAberto(abrir)
        if (!abrir) setErro(null)
      }}
    >
      <AlertDialogTrigger asChild>
        <Button variant="ghost" className="justify-self-start text-destructive hover:text-destructive">
          <Trash2Icon aria-hidden />
          Excluir lembrete
        </Button>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Excluir lembrete?</AlertDialogTitle>
          <AlertDialogDescription>
            &ldquo;{lembrete.texto}&rdquo; será excluído. Não dá para desfazer.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <ErroForm mensagem={erro} />
        <AlertDialogFooter>
          <AlertDialogCancel disabled={excluindo}>Cancelar</AlertDialogCancel>
          {/* Botão comum: a ação da Radix fecharia o dialog antes da resposta da API. */}
          <Button variant="destructive" onClick={confirmar} disabled={excluindo} aria-busy={excluindo}>
            {excluindo && <Loader2Icon className="animate-spin" aria-hidden />}
            Excluir
          </Button>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
