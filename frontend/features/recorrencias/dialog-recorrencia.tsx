"use client"

import { useState } from "react"
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
import { useCarteira } from "@/features/carteira/contexto"
import { criarRecorrencia, editarRecorrencia } from "@/lib/api/recorrencias"
import type { Categoria, Recorrencia, RecorrenciaIn } from "@/lib/api/types"
import { VALOR_MAXIMO } from "@/lib/format"
import { aplicarErroApi, regras } from "@/lib/forms"

// Espelha backend/app/schemas/recorrencia.py; a API segue como fonte da verdade.
const MAX_DESCRICAO = 200

const esquema = z.object({
  descricao: regras.obrigatorio(MAX_DESCRICAO),
  valor: z
    .number()
    .int()
    .min(1, "Informe um valor maior que zero.")
    .max(VALOR_MAXIMO, "Valor acima do limite."),
  categoria_id: z.string().min(1, "Escolha uma categoria."),
  dia: regras.diaDoMes,
})

type Valores = z.infer<typeof esquema>

type Props = {
  aberto: boolean
  aoMudar: (aberto: boolean) => void
  /** Só as ativas. */
  categorias: Categoria[]
  /** Presente ao editar. */
  recorrencia?: Recorrencia
}

export function DialogRecorrencia({ aberto, aoMudar, categorias, recorrencia }: Props) {
  return (
    <Dialog open={aberto} onOpenChange={aoMudar}>
      <DialogContent className="max-h-[calc(100dvh-2rem)] overflow-y-auto p-6 sm:max-w-md">
        <DialogHeader className="mb-2">
          <DialogTitle className="text-xl">{recorrencia ? "Editar recorrência" : "Nova recorrência"}</DialogTitle>
          <DialogDescription>
            {recorrencia
              ? "As mudanças valem a partir do próximo ciclo. O previsto já gerado neste ciclo não muda."
              : "Gasto ou renda fixa, como aluguel ou internet. Cada ciclo ganha um previsto no dia escolhido."}
          </DialogDescription>
        </DialogHeader>
        {/* Monta de novo a cada abertura para começar sem valores e erros antigos. */}
        {aberto && (
          <FormRecorrencia categorias={categorias} recorrencia={recorrencia} aoConcluir={() => aoMudar(false)} />
        )}
      </DialogContent>
    </Dialog>
  )
}

function FormRecorrencia({
  categorias,
  recorrencia,
  aoConcluir,
}: {
  categorias: Categoria[]
  recorrencia?: Recorrencia
  aoConcluir: () => void
}) {
  const router = useRouter()
  const [erroGeral, setErroGeral] = useState<string | null>(null)
  const form = useForm<Valores>({
    resolver: zodResolver(esquema),
    defaultValues: recorrencia
      ? {
          descricao: recorrencia.descricao,
          valor: recorrencia.valor,
          categoria_id: String(recorrencia.categoria_id),
          dia: String(recorrencia.dia),
        }
      : { descricao: "", valor: 0, categoria_id: "", dia: "" },
  })
  const { errors, isSubmitting, isDirty } = form.formState

  const { carteira } = useCarteira()

  async function enviar(valores: Valores) {
    setErroGeral(null)
    const dados: Omit<RecorrenciaIn, "carteira"> = {
      descricao: valores.descricao,
      valor: valores.valor,
      categoria_id: Number(valores.categoria_id),
      dia: Number(valores.dia),
    }
    try {
      if (recorrencia) {
        await editarRecorrencia(recorrencia.id, dados)
        toast.success("Recorrência salva. Vale a partir do próximo ciclo.")
      } else {
        await criarRecorrencia({ ...dados, carteira })
        toast.success("Recorrência criada. Ela gera um previsto em cada ciclo.")
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
          label="Descrição"
          autoFocus
          autoComplete="off"
          placeholder="Ex.: Internet"
          maxLength={MAX_DESCRICAO}
          erro={errors.descricao?.message}
          {...form.register("descricao")}
        />
        <div className="grid gap-5 sm:grid-cols-[1fr_7rem]">
          <Controller
            control={form.control}
            name="valor"
            render={({ field }) => (
              <CampoValor
                label="Valor"
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
            label="Dia do mês"
            type="number"
            inputMode="numeric"
            min={1}
            max={31}
            erro={errors.dia?.message}
            {...form.register("dia")}
          />
        </div>
        <Controller
          control={form.control}
          name="categoria_id"
          render={({ field }) => (
            <CampoCategoria
              categorias={categorias}
              semSalario
              name={field.name}
              ref={field.ref}
              value={field.value}
              onBlur={field.onBlur}
              onChange={field.onChange}
              descricao="Entrada ou saída vem da categoria. O salário não é recorrência: ele é lançado quando entra."
              erro={errors.categoria_id?.message}
            />
          )}
        />
        <ErroForm mensagem={erroGeral} />
        <div>
          <BotaoEnviar enviando={isSubmitting} disabled={Boolean(recorrencia) && !isDirty}>
            {recorrencia ? "Salvar alterações" : "Criar recorrência"}
          </BotaoEnviar>
        </div>
      </FieldGroup>
    </form>
  )
}
