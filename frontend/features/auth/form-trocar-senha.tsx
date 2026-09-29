"use client"

import { useState } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"

import { BotaoEnviar } from "@/components/forms/botao-enviar"
import { CampoSenha } from "@/components/forms/campo-senha"
import { ErroForm } from "@/components/forms/erro-form"
import { FieldGroup } from "@/components/ui/field"
import { trocarSenha } from "@/lib/api/auth"
import { aplicarErroApi, regras } from "@/lib/forms"

const esquema = z
  .object({
    senha_atual: z.string().min(1, "Informe sua senha atual."),
    nova_senha: regras.senha,
    confirmacao: z.string(),
  })
  .refine((v) => v.nova_senha === v.confirmacao, {
    path: ["confirmacao"],
    message: "As senhas não são iguais.",
  })
  .refine((v) => v.nova_senha !== v.senha_atual, {
    path: ["nova_senha"],
    message: "A nova senha deve ser diferente da atual.",
  })

type Valores = z.infer<typeof esquema>

type Props = {
  /** Chamado depois que a API confirma a troca. */
  aoTrocar: () => void
  textoBotao?: string
  className?: string
}

export function FormTrocarSenha({ aoTrocar, textoBotao = "Trocar senha", className }: Props) {
  const [erroGeral, setErroGeral] = useState<string | null>(null)
  const form = useForm<Valores>({
    resolver: zodResolver(esquema),
    defaultValues: { senha_atual: "", nova_senha: "", confirmacao: "" },
  })
  const { errors, isSubmitting } = form.formState

  async function enviar({ senha_atual, nova_senha }: Valores) {
    setErroGeral(null)
    try {
      await trocarSenha({ senha_atual, nova_senha })
      form.reset()
      aoTrocar()
    } catch (erro) {
      setErroGeral(aplicarErroApi(form, erro, { senha_atual_incorreta: "senha_atual" }))
    }
  }

  return (
    <form onSubmit={form.handleSubmit(enviar)} noValidate className={className}>
      <FieldGroup>
        <CampoSenha
          label="Senha atual"
          autoComplete="current-password"
          erro={errors.senha_atual?.message}
          {...form.register("senha_atual")}
        />
        <CampoSenha
          label="Nova senha"
          autoComplete="new-password"
          descricao="Pelo menos 8 caracteres, com letras e números."
          erro={errors.nova_senha?.message}
          {...form.register("nova_senha")}
        />
        <CampoSenha
          label="Repita a nova senha"
          autoComplete="new-password"
          erro={errors.confirmacao?.message}
          {...form.register("confirmacao")}
        />
        <ErroForm mensagem={erroGeral} />
        <div>
          <BotaoEnviar enviando={isSubmitting}>{textoBotao}</BotaoEnviar>
        </div>
      </FieldGroup>
    </form>
  )
}
