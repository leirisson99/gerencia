"use client"

import { useState } from "react"
import { Controller, useForm, useWatch } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"

import { BotaoEnviar } from "@/components/forms/botao-enviar"
import { Campo } from "@/components/forms/campo"
import { CampoCategoria } from "@/components/forms/campo-categoria"
import { CampoValor } from "@/components/forms/campo-valor"
import { ErroForm } from "@/components/forms/erro-form"
import { Checkbox } from "@/components/ui/checkbox"
import { Field, FieldGroup, FieldLabel } from "@/components/ui/field"
import { criarLancamento, editarLancamento } from "@/lib/api/lancamentos"
import type { Categoria, Lancamento, LancamentoIn } from "@/lib/api/types"
import { acharSalario, eSalario } from "@/lib/categorias"
import { VALOR_MAXIMO, hojeSaoPaulo } from "@/lib/format"
import { aplicarErroApi } from "@/lib/forms"

const MAX_DESCRICAO = 200

// Regras espelhadas de backend/app/schemas/lancamento.py; a API segue como fonte da verdade.
const esquema = z.object({
  valor: z
    .number()
    .int()
    .min(1, "Informe um valor maior que zero.")
    .max(VALOR_MAXIMO, "Valor acima do limite."),
  categoria_id: z.string().min(1, "Escolha uma categoria."),
  data: z.string().min(1, "Campo obrigatório."),
  descricao: z.string().trim().max(MAX_DESCRICAO, `Máximo de ${MAX_DESCRICAO} caracteres.`),
  previsto: z.boolean(),
})

type Valores = z.infer<typeof esquema>

type Props = {
  categorias: Categoria[]
  /** Valor do último salário, sugerido ao escolher "Salário" num lançamento novo. */
  sugestaoSalario: number | null
  /** Presente ao editar. */
  lancamento?: Lancamento
  /** Categoria já escolhida ao abrir um lançamento novo. */
  categoriaInicial?: Categoria
  aoConcluir: (lancamento: Lancamento) => void
}

export function FormLancamento({
  categorias,
  sugestaoSalario,
  lancamento,
  categoriaInicial,
  aoConcluir,
}: Props) {
  const [erroGeral, setErroGeral] = useState<string | null>(null)
  const hoje = hojeSaoPaulo()
  const salario = acharSalario(categorias)
  // A categoria da parcela vem da dívida e não muda (a API recusa com 422).
  const eParcela = lancamento?.divida_id != null

  const form = useForm<Valores>({
    resolver: zodResolver(esquema),
    defaultValues: lancamento
      ? {
          valor: lancamento.valor,
          categoria_id: String(lancamento.categoria_id),
          data: lancamento.data,
          descricao: lancamento.descricao ?? "",
          previsto: lancamento.status === "previsto",
        }
      : {
          valor: (categoriaInicial && eSalario(categoriaInicial) && sugestaoSalario) || 0,
          categoria_id: categoriaInicial ? String(categoriaInicial.id) : "",
          data: hoje,
          descricao: "",
          previsto: false,
        },
  })
  const { errors, isSubmitting, isDirty } = form.formState
  const categoriaEscolhida = useWatch({ control: form.control, name: "categoria_id" })
  const escolheuSalario = salario !== undefined && categoriaEscolhida === String(salario.id)

  function aoEscolherCategoria(valor: string) {
    if (salario && valor === String(salario.id)) {
      // Salário é lançado quando entra: nunca previsto nem com data futura.
      form.setValue("previsto", false)
      if (form.getValues("data") > hoje) form.setValue("data", hoje)
      if (!lancamento && form.getValues("valor") === 0 && sugestaoSalario) {
        form.setValue("valor", sugestaoSalario)
      }
    }
  }

  async function enviar(valores: Valores) {
    setErroGeral(null)
    if (escolheuSalario && valores.data > hoje) {
      form.setError("data", { message: "O salário é lançado quando entra. Use hoje ou uma data passada." })
      return
    }
    const dados: LancamentoIn = {
      valor: valores.valor,
      categoria_id: Number(valores.categoria_id),
      data: valores.data,
      descricao: valores.descricao || null,
      status: valores.previsto ? "previsto" : "realizado",
    }
    try {
      if (!lancamento) return aoConcluir(await criarLancamento(dados))
      const { categoria_id, ...semCategoria } = dados
      aoConcluir(await editarLancamento(lancamento.id, eParcela ? semCategoria : { ...semCategoria, categoria_id }))
    } catch (erro) {
      setErroGeral(
        aplicarErroApi(form, erro, {
          salario_necessario: "categoria_id",
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

        <Controller
          control={form.control}
          name="categoria_id"
          render={({ field }) => (
            <CampoCategoria
              categorias={categorias}
              name={field.name}
              ref={field.ref}
              value={field.value}
              onBlur={field.onBlur}
              onChange={(valor) => {
                field.onChange(valor)
                aoEscolherCategoria(valor)
              }}
              disabled={eParcela}
              descricao={eParcela ? `Parcela ${lancamento?.parcela_num} de uma dívida: a categoria vem da dívida.` : undefined}
              erro={errors.categoria_id?.message}
            />
          )}
        />

        <Campo
          label="Data"
          type="date"
          max={escolheuSalario ? hoje : undefined}
          descricao={escolheuSalario ? "O salário abre um ciclo nesta data." : undefined}
          erro={errors.data?.message}
          {...form.register("data")}
        />

        <Campo
          label="Descrição"
          autoComplete="off"
          maxLength={MAX_DESCRICAO}
          descricao="Opcional."
          erro={errors.descricao?.message}
          {...form.register("descricao")}
        />

        {!escolheuSalario && (
          <Controller
            control={form.control}
            name="previsto"
            render={({ field }) => (
              <Field orientation="horizontal">
                <Checkbox
                  id="lancamento-previsto"
                  name={field.name}
                  ref={field.ref}
                  checked={field.value}
                  onCheckedChange={(marcado) => field.onChange(marcado === true)}
                />
                <FieldLabel htmlFor="lancamento-previsto" className="font-normal">
                  Ainda não aconteceu (previsto)
                </FieldLabel>
              </Field>
            )}
          />
        )}

        <ErroForm mensagem={erroGeral} />
        <div>
          <BotaoEnviar enviando={isSubmitting} disabled={Boolean(lancamento) && !isDirty}>
            {lancamento ? "Salvar alterações" : "Lançar"}
          </BotaoEnviar>
        </div>
      </FieldGroup>
    </form>
  )
}
