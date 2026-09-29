"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"

import { BotaoEnviar } from "@/components/forms/botao-enviar"
import { Campo } from "@/components/forms/campo"
import { CampoSenha } from "@/components/forms/campo-senha"
import { ErroForm } from "@/components/forms/erro-form"
import { FieldGroup } from "@/components/ui/field"
import { entrar } from "@/lib/api/auth"
import { aplicarErroApi } from "@/lib/forms"

// Sem validar formato: o login responde sempre a mesma mensagem genérica.
const esquema = z.object({
  email: z.string().trim().min(1, "Informe seu e-mail."),
  senha: z.string().min(1, "Informe sua senha."),
})

type Valores = z.infer<typeof esquema>

export function FormEntrar() {
  const router = useRouter()
  const [erroGeral, setErroGeral] = useState<string | null>(null)
  const form = useForm<Valores>({
    resolver: zodResolver(esquema),
    defaultValues: { email: "", senha: "" },
  })
  const { errors, isSubmitting } = form.formState

  async function enviar(valores: Valores) {
    setErroGeral(null)
    try {
      const usuario = await entrar(valores)
      if (usuario.troca_senha_obrigatoria) router.replace("/trocar-senha")
      else router.replace(usuario.papel === "admin" ? "/admin" : "/")
      router.refresh()
    } catch (erro) {
      setErroGeral(aplicarErroApi(form, erro))
    }
  }

  return (
    <form onSubmit={form.handleSubmit(enviar)} noValidate>
      <FieldGroup>
        <Campo
          label="E-mail"
          type="email"
          autoComplete="email"
          inputMode="email"
          autoFocus
          erro={errors.email?.message}
          {...form.register("email")}
        />
        <CampoSenha
          label="Senha"
          autoComplete="current-password"
          erro={errors.senha?.message}
          {...form.register("senha")}
        />
        <ErroForm mensagem={erroGeral} />
        <BotaoEnviar enviando={isSubmitting} size="lg" className="w-full">
          Entrar
        </BotaoEnviar>
      </FieldGroup>
    </form>
  )
}
