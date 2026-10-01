"use client"

import { useState, type ReactNode } from "react"
import { useRouter } from "next/navigation"
import { Controller, useForm } from "react-hook-form"
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
import { FieldGroup } from "@/components/ui/field"
import { criarServico, editarServico } from "@/lib/api/servicos"
import type { Categoria, Servico, ServicoIn } from "@/lib/api/types"
import { VALOR_MAXIMO, formatarData, hojeSaoPaulo } from "@/lib/format"
import { aplicarErroApi, regras } from "@/lib/forms"

// Espelha backend/app/schemas/servico.py; a API segue como fonte da verdade.
const MAX_CLIENTE = 120
const MAX_DESCRICAO = 200

const esquema = z.object({
  cliente: regras.obrigatorio(MAX_CLIENTE),
  descricao: z.string().trim().max(MAX_DESCRICAO, `Máximo de ${MAX_DESCRICAO} caracteres.`),
  valor: z
    .number()
    .int()
    .min(1, "Informe um valor maior que zero.")
    .max(VALOR_MAXIMO, "Valor acima do limite."),
  data_prevista: z.string().min(1, "Campo obrigatório."),
  categoria_id: z.string().min(1, "Escolha uma categoria."),
})

type Valores = z.infer<typeof esquema>

type Props = {
  aberto: boolean
  aoMudar: (aberto: boolean) => void
  /** Só as ativas. */
  categorias: Categoria[]
  /** Presente ao editar; só serviços ainda não recebidos. */
  servico?: Servico
  /** Ações extras abaixo do formulário (ex.: excluir). */
  rodape?: ReactNode
}

/** Criar ou editar um serviço a receber. Ao salvar, fecha e recarrega os dados da página. */
export function DialogServico({ aberto, aoMudar, categorias, servico, rodape }: Props) {
  return (
    <Dialog open={aberto} onOpenChange={aoMudar}>
      <DialogContent className="max-h-[calc(100dvh-2rem)] overflow-y-auto p-6 sm:max-w-md">
        <DialogHeader className="mb-2">
          <DialogTitle className="text-xl">{servico ? "Editar serviço" : "Novo serviço"}</DialogTitle>
          <DialogDescription>
            Vira uma entrada prevista na data combinada. Só conta no saldo quando você marca o
            recebimento.
          </DialogDescription>
        </DialogHeader>
        {/* Monta de novo a cada abertura para começar sem valores e erros antigos. */}
        {aberto && (
          <FormServico categorias={categorias} servico={servico} aoConcluir={() => aoMudar(false)} />
        )}
        {rodape}
      </DialogContent>
    </Dialog>
  )
}

function FormServico({
  categorias,
  servico,
  aoConcluir,
}: {
  categorias: Categoria[]
  servico?: Servico
  aoConcluir: () => void
}) {
  const router = useRouter()
  const [erroGeral, setErroGeral] = useState<string | null>(null)
  const form = useForm<Valores>({
    resolver: zodResolver(esquema),
    defaultValues: servico
      ? {
          cliente: servico.cliente,
          descricao: servico.descricao ?? "",
          valor: servico.valor,
          data_prevista: servico.data_prevista,
          categoria_id: String(servico.categoria_id),
        }
      : { cliente: "", descricao: "", valor: 0, data_prevista: hojeSaoPaulo(), categoria_id: "" },
  })
  const { errors, isSubmitting, isDirty } = form.formState

  async function enviar(valores: Valores) {
    setErroGeral(null)
    const dados: ServicoIn = {
      cliente: valores.cliente,
      descricao: valores.descricao || null,
      valor: valores.valor,
      data_prevista: valores.data_prevista,
      categoria_id: Number(valores.categoria_id),
    }
    try {
      if (servico) {
        await editarServico(servico.id, dados)
        toast.success("Serviço salvo.")
      } else {
        const criado = await criarServico(dados)
        toast.success(`Serviço previsto para ${formatarData(criado.data_prevista)}.`)
      }
      aoConcluir()
      router.refresh()
    } catch (erro) {
      setErroGeral(
        aplicarErroApi(form, erro, {
          salario_necessario: "data_prevista",
          antes_do_primeiro_ciclo: "data_prevista",
        })
      )
    }
  }

  return (
    <form onSubmit={form.handleSubmit(enviar)} noValidate>
      <FieldGroup>
        <Campo
          label="Cliente"
          autoFocus
          autoComplete="off"
          maxLength={MAX_CLIENTE}
          erro={errors.cliente?.message}
          {...form.register("cliente")}
        />
        <Campo
          label="Descrição"
          autoComplete="off"
          maxLength={MAX_DESCRICAO}
          placeholder="Ex.: Site institucional"
          descricao="Opcional."
          erro={errors.descricao?.message}
          {...form.register("descricao")}
        />
        <div className="grid gap-5 sm:grid-cols-2">
          <Controller
            control={form.control}
            name="valor"
            render={({ field }) => (
              <CampoValor
                label="Valor combinado"
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
            label="Data prevista"
            type="date"
            erro={errors.data_prevista?.message}
            {...form.register("data_prevista")}
          />
        </div>
        <Controller
          control={form.control}
          name="categoria_id"
          render={({ field }) => (
            <CampoCategoria
              categorias={categorias}
              tipo="entrada"
              semSalario
              name={field.name}
              ref={field.ref}
              value={field.value}
              onBlur={field.onBlur}
              onChange={field.onChange}
              erro={errors.categoria_id?.message}
            />
          )}
        />
        <ErroForm mensagem={erroGeral} />
        <div>
          <BotaoEnviar enviando={isSubmitting} disabled={Boolean(servico) && !isDirty}>
            {servico ? "Salvar alterações" : "Criar serviço"}
          </BotaoEnviar>
        </div>
      </FieldGroup>
    </form>
  )
}
