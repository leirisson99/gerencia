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
import { Field, FieldDescription, FieldGroup, FieldLabel } from "@/components/ui/field"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { criarDivida } from "@/lib/api/dividas"
import type { Categoria, Direcao, DividaIn, FormaPagamento } from "@/lib/api/types"
import { VALOR_MAXIMO, formatarCentavos, hojeSaoPaulo } from "@/lib/format"
import { aplicarErroApi, regras } from "@/lib/forms"
import { DIRECOES, FORMAS } from "./rotulos"

// Espelha backend/app/schemas/divida.py; a API segue como fonte da verdade.
const MAX_DESCRICAO = 200
const MAX_PESSOA = 120
const MAX_PARCELAS = 120

const esquema = z
  .object({
    direcao: z.enum(["devo", "me_devem"]),
    descricao: regras.obrigatorio(MAX_DESCRICAO),
    pessoa: regras.obrigatorio(MAX_PESSOA),
    valor_total: z
      .number()
      .int()
      .min(1, "Informe um valor maior que zero.")
      .max(VALOR_MAXIMO, "Valor acima do limite."),
    parcelas: z.string().refine((v) => /^\d+$/.test(v) && Number(v) >= 1 && Number(v) <= MAX_PARCELAS, {
      message: `Informe de 1 a ${MAX_PARCELAS} parcelas.`,
    }),
    forma_pagamento: z.enum(["pix", "boleto", "cartao", "dinheiro"]),
    dia_vencimento: regras.diaDoMes,
    data_inicio: z.string().min(1, "Campo obrigatório."),
    categoria_id: z.string().min(1, "Escolha uma categoria."),
  })
  .refine((v) => !(v.forma_pagamento === "cartao" && v.direcao === "me_devem"), {
    path: ["forma_pagamento"],
    message: "Cartão só vale para o que você deve.",
  })

type Valores = z.infer<typeof esquema>

type Props = {
  aberto: boolean
  aoMudar: (aberto: boolean) => void
  /** Só as ativas. */
  categorias: Categoria[]
}

export function DialogDivida({ aberto, aoMudar, categorias }: Props) {
  return (
    <Dialog open={aberto} onOpenChange={aoMudar}>
      <DialogContent className="max-h-[calc(100dvh-2rem)] overflow-y-auto p-6 sm:max-w-lg">
        <DialogHeader className="mb-2">
          <DialogTitle className="text-xl">Nova dívida</DialogTitle>
          <DialogDescription>
            As parcelas viram lançamentos previstos, um por mês no dia do vencimento. Depois é só marcar
            cada uma como paga ou recebida.
          </DialogDescription>
        </DialogHeader>
        {/* Monta de novo a cada abertura para começar sem valores e erros antigos. */}
        {aberto && <FormDivida categorias={categorias} aoConcluir={() => aoMudar(false)} />}
      </DialogContent>
    </Dialog>
  )
}

function FormDivida({ categorias, aoConcluir }: { categorias: Categoria[]; aoConcluir: () => void }) {
  const router = useRouter()
  const [erroGeral, setErroGeral] = useState<string | null>(null)
  const form = useForm<Valores>({
    resolver: zodResolver(esquema),
    defaultValues: {
      direcao: "devo",
      descricao: "",
      pessoa: "",
      valor_total: 0,
      parcelas: "1",
      forma_pagamento: "pix",
      dia_vencimento: "",
      data_inicio: hojeSaoPaulo(),
      categoria_id: "",
    },
  })
  const { errors, isSubmitting } = form.formState
  const [direcao, forma, valorTotal, parcelas] = useWatch({
    control: form.control,
    name: ["direcao", "forma_pagamento", "valor_total", "parcelas"],
  })
  const qtdParcelas = /^\d+$/.test(parcelas) ? Number(parcelas) : 0

  function aoMudarDirecao(nova: Direcao) {
    // A categoria depende da direção (saída se devo, entrada se me devem): recomeça a escolha.
    form.setValue("categoria_id", "")
    if (nova === "me_devem" && form.getValues("forma_pagamento") === "cartao") {
      form.setValue("forma_pagamento", "pix")
    }
  }

  async function enviar(v: Valores) {
    setErroGeral(null)
    const dados: DividaIn = {
      direcao: v.direcao,
      descricao: v.descricao,
      pessoa: v.pessoa,
      valor_total: v.valor_total,
      parcelas: Number(v.parcelas),
      forma_pagamento: v.forma_pagamento,
      dia_vencimento: Number(v.dia_vencimento),
      data_inicio: v.data_inicio,
      categoria_id: Number(v.categoria_id),
    }
    try {
      const divida = await criarDivida(dados)
      toast.success(`Dívida criada com ${divida.parcelas} ${divida.parcelas === 1 ? "parcela" : "parcelas"}.`)
      aoConcluir()
      router.push(`/dividas/${divida.id}`)
      router.refresh()
    } catch (erro) {
      setErroGeral(
        aplicarErroApi(form, erro, {
          salario_necessario: "data_inicio",
          antes_do_primeiro_ciclo: "data_inicio",
        })
      )
    }
  }

  return (
    <form onSubmit={form.handleSubmit(enviar)} noValidate>
      <FieldGroup>
        <Controller
          control={form.control}
          name="direcao"
          render={({ field }) => (
            <Field>
              <FieldLabel htmlFor="divida-direcao">Tipo</FieldLabel>
              <Select
                name={field.name}
                value={field.value}
                onValueChange={(valor) => {
                  field.onChange(valor)
                  aoMudarDirecao(valor as Direcao)
                }}
              >
                <SelectTrigger id="divida-direcao" ref={field.ref} className="w-full text-base data-[size=default]:h-10">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent position="popper">
                  {(Object.keys(DIRECOES) as Direcao[]).map((d) => (
                    <SelectItem key={d} value={d}>
                      {DIRECOES[d]}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </Field>
          )}
        />

        <div className="grid gap-5 sm:grid-cols-2">
          <Campo
            label="Descrição"
            autoFocus
            autoComplete="off"
            placeholder="Ex.: Notebook"
            maxLength={MAX_DESCRICAO}
            erro={errors.descricao?.message}
            {...form.register("descricao")}
          />
          <Campo
            label={direcao === "devo" ? "Para quem" : "Quem deve"}
            autoComplete="off"
            placeholder={direcao === "devo" ? "Ex.: Loja X" : "Ex.: João"}
            maxLength={MAX_PESSOA}
            erro={errors.pessoa?.message}
            {...form.register("pessoa")}
          />
        </div>

        <div className="grid gap-5 sm:grid-cols-[1fr_7rem]">
          <Controller
            control={form.control}
            name="valor_total"
            render={({ field }) => (
              <CampoValor
                label="Valor total"
                erro={errors.valor_total?.message}
                name={field.name}
                ref={field.ref}
                onBlur={field.onBlur}
                value={field.value}
                onChange={field.onChange}
              />
            )}
          />
          <Campo
            label="Parcelas"
            type="number"
            inputMode="numeric"
            min={1}
            max={MAX_PARCELAS}
            erro={errors.parcelas?.message}
            {...form.register("parcelas")}
          />
        </div>
        {valorTotal > 0 && qtdParcelas > 1 && (
          // Só uma prévia: a divisão oficial (resto de centavos na última) é feita pela API.
          <p className="-mt-3 text-sm text-muted-foreground">
            {qtdParcelas} parcelas de cerca de {formatarCentavos(Math.floor(valorTotal / qtdParcelas))}.
          </p>
        )}

        <div className="grid gap-5 sm:grid-cols-2">
          <Campo
            label="Primeira parcela a partir de"
            type="date"
            erro={errors.data_inicio?.message}
            {...form.register("data_inicio")}
          />
          <Campo
            label="Dia do vencimento"
            type="number"
            inputMode="numeric"
            min={1}
            max={31}
            erro={errors.dia_vencimento?.message}
            {...form.register("dia_vencimento")}
          />
        </div>

        <Controller
          control={form.control}
          name="forma_pagamento"
          render={({ field }) => (
            <Field data-invalid={errors.forma_pagamento ? true : undefined}>
              <FieldLabel htmlFor="divida-forma">Forma de pagamento</FieldLabel>
              <Select name={field.name} value={field.value} onValueChange={field.onChange}>
                <SelectTrigger
                  id="divida-forma"
                  ref={field.ref}
                  aria-invalid={errors.forma_pagamento ? true : undefined}
                  className="w-full text-base data-[size=default]:h-10"
                >
                  <SelectValue />
                </SelectTrigger>
                <SelectContent position="popper">
                  {(Object.keys(FORMAS) as FormaPagamento[]).map((f) => (
                    <SelectItem key={f} value={f} disabled={f === "cartao" && direcao === "me_devem"}>
                      {FORMAS[f]}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {errors.forma_pagamento ? (
                <p role="alert" className="text-sm text-destructive">
                  {errors.forma_pagamento.message}
                </p>
              ) : (
                forma === "cartao" && (
                  <FieldDescription>
                    Parcelas no cartão não entram no saldo: o cartão já entra como a fatura.
                  </FieldDescription>
                )
              )}
            </Field>
          )}
        />

        <Controller
          control={form.control}
          name="categoria_id"
          render={({ field }) => (
            <CampoCategoria
              categorias={categorias}
              tipo={direcao === "devo" ? "saida" : "entrada"}
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
          <BotaoEnviar enviando={isSubmitting}>Criar dívida</BotaoEnviar>
        </div>
      </FieldGroup>
    </form>
  )
}
