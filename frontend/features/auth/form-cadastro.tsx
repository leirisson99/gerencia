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
import { cadastrar } from "@/lib/api/auth"
import { mascararTelefone } from "@/lib/format"
import { aplicarErroApi, regras } from "@/lib/forms"

const esquema = z.object({
  nome: regras.obrigatorio(120),
  email: regras.email,
  telefone: regras.telefone,
  cargo: regras.obrigatorio(80),
  senha: regras.senha,
  data_nascimento: regras.dataOpcional,
})

type Valores = z.infer<typeof esquema>

export function FormCadastro() {
  const router = useRouter()
  const [erroGeral, setErroGeral] = useState<string | null>(null)
  const form = useForm<Valores>({
    resolver: zodResolver(esquema),
    defaultValues: { nome: "", email: "", telefone: "", cargo: "", senha: "", data_nascimento: "" },
  })
  const { errors, isSubmitting } = form.formState
  const telefone = form.register("telefone")

  async function enviar(valores: Valores) {
    setErroGeral(null)
    try {
      await cadastrar({ ...valores, data_nascimento: valores.data_nascimento || null })
      router.replace("/")
      router.refresh()
    } catch (erro) {
      setErroGeral(aplicarErroApi(form, erro, { email_ja_cadastrado: "email" }))
    }
  }

  return (
    <form onSubmit={form.handleSubmit(enviar)} noValidate>
      <FieldGroup>
        <Campo
          label="Nome"
          autoComplete="name"
          autoFocus
          erro={errors.nome?.message}
          {...form.register("nome")}
        />
        <Campo
          label="E-mail"
          type="email"
          autoComplete="email"
          inputMode="email"
          erro={errors.email?.message}
          {...form.register("email")}
        />
        <div className="grid gap-5 sm:grid-cols-2">
          <Campo
            label="Telefone"
            type="tel"
            autoComplete="tel-national"
            inputMode="numeric"
            placeholder="(11) 98765-4321"
            erro={errors.telefone?.message}
            {...telefone}
            onChange={(e) => {
              e.target.value = mascararTelefone(e.target.value)
              return telefone.onChange(e)
            }}
          />
          <Campo
            label="Data de nascimento"
            type="date"
            autoComplete="bday"
            descricao="Opcional"
            erro={errors.data_nascimento?.message}
            {...form.register("data_nascimento")}
          />
        </div>
        <Campo
          label="Cargo"
          autoComplete="organization-title"
          erro={errors.cargo?.message}
          {...form.register("cargo")}
        />
        <CampoSenha
          label="Senha"
          autoComplete="new-password"
          descricao="Pelo menos 8 caracteres, com letras e números."
          erro={errors.senha?.message}
          {...form.register("senha")}
        />
        <ErroForm mensagem={erroGeral} />
        <BotaoEnviar enviando={isSubmitting} size="lg" className="w-full">
          Criar conta
        </BotaoEnviar>
      </FieldGroup>
    </form>
  )
}
