import type { FieldValues, Path, UseFormReturn } from "react-hook-form"
import { z } from "zod"

import { ApiError } from "@/lib/api/client"

// Regras espelhadas de backend/app/domain/usuario.py. A API continua sendo a fonte da verdade:
// estas validações só antecipam o erro para quem está digitando.
export const regras = {
  obrigatorio: (max: number) =>
    z
      .string()
      .trim()
      .min(1, "Campo obrigatório.")
      .max(max, `Máximo de ${max} caracteres.`),
  email: z.string().trim().min(1, "Campo obrigatório.").pipe(z.email("E-mail inválido.")),
  telefone: z
    .string()
    .min(1, "Campo obrigatório.")
    .refine((v) => [10, 11].includes(v.replace(/\D/g, "").length), {
      message: "Informe DDD e número, com 10 ou 11 dígitos.",
    }),
  senha: z
    .string()
    .min(8, "A senha deve ter entre 8 e 128 caracteres.")
    .max(128, "A senha deve ter entre 8 e 128 caracteres.")
    .refine((v) => /\p{L}/u.test(v) && /\d/.test(v), {
      message: "A senha deve ter pelo menos uma letra e um número.",
    }),
  /** Vazio vira `null` ao enviar. */
  dataOpcional: z.string(),
  /** Dia do mês como texto do campo; converta com `Number` ao enviar. */
  diaDoMes: z
    .string()
    .refine((v) => /^\d{1,2}$/.test(v) && Number(v) >= 1 && Number(v) <= 31, {
      message: "Informe um dia de 1 a 31.",
    }),
}

export const MENSAGEM_GENERICA = "Algo deu errado. Tente de novo."

/**
 * Leva os erros de campo da API para o formulário.
 * Devolve a mensagem geral quando o erro não pertence a nenhum campo visível.
 */
export function aplicarErroApi<T extends FieldValues>(
  form: UseFormReturn<T>,
  erro: unknown,
  /** Erros sem `campos` que pertencem a um campo específico, por código. */
  codigoParaCampo: Record<string, Path<T>> = {}
): string | null {
  if (!(erro instanceof ApiError)) return MENSAGEM_GENERICA

  const campoDoCodigo = codigoParaCampo[erro.codigo]
  if (campoDoCodigo) {
    form.setError(campoDoCodigo, { message: erro.message }, { shouldFocus: true })
    return null
  }

  const conhecidos = new Set(Object.keys(form.getValues()))
  let aplicou = false
  for (const [campo, mensagem] of Object.entries(erro.campos)) {
    if (!conhecidos.has(campo)) continue
    form.setError(campo as Path<T>, { message: mensagem }, { shouldFocus: !aplicou })
    aplicou = true
  }
  return aplicou ? null : erro.message
}
